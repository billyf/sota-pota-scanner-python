import time
import tkinter as tk
from tkinter import ttk
from typing import List

import helpers
from activation_info import ActivationInfo
from data_query import data_fetcher
from rig.rig_control import Rig
from storage import worked_history
from storage.settings import Settings

SHOW_SPOTA_TWICE = False
"""If true, a combination SOTA+POTA spot will show separate listings"""

MAX_SPOTS_QUERY = 50

RIG_CONFIG_FILE = helpers.local_file_path(__file__, "rig.cfg")


def matches_worked(spot: ActivationInfo, worked_spot: ActivationInfo):
    """If the call and park match"""
    return spot.callsign == worked_spot.callsign \
        and spot.description == worked_spot.description
    #       and spot.mode == worked_spot.mode


def get_row_for_table(spot: ActivationInfo):
    return [spot_age_mins(spot), spot.callsign,
            spot.description,
            spot.frequency, spot.mode.mode_str]


def setup_headers(ac, tv, column_labels, column_widths):
    for i in range(len(column_labels)):
        tv.column(ac[i], width=column_widths[i], anchor=tk.CENTER)
        tv.heading(ac[i], text=column_labels[i])


def spot_age_mins(spot):
    return spot.spot_age_mins()


def get_tags_for_spot(spot):
    return spot.activation_type,


def fill_treeview(tv, spots):
    tv.delete(*tv.get_children())
    spots.sort(key=spot_age_mins)
    for index, spot in enumerate(spots):
        tv.insert('', 'end', values=get_row_for_table(spot), iid=index, tags=get_tags_for_spot(spot))
    # the tags from get_tags_for_spot() can be used to distinguish rows - must match spot.activation_type
    tv.tag_configure('sota', background='lightblue')
    # tv.tag_configure('pota', background='white')


class ScannerView:
    def __init__(self, settings: Settings, rig_control: Rig):
        self.settings = settings
        self.rig_control = rig_control
        self.data_fetcher = data_fetcher.DataFetcher()
        self.top_spots = []
        self.worked_spots = worked_history.load_worked_history()  # we've worked this activator+park already
        self.root = tk.Tk()
        iconfile = helpers.local_file_path(__file__, "icon.png")
        img = tk.Image("photo", file=iconfile)
        self.root.tk.call('wm', 'iconphoto', self.root._w, img)
        self.root.title("SOTA/POTA spots")
        tk.Label(self.root, text='Active spots').pack()
        column_labels = ('Age', 'Call', 'Summit/Park', 'MHz', 'Mode')
        column_widths = ('40', '110', '130', '100', '50')
        ac = ('all', 'n', 'e', 's', 'ne')

        frame_top = tk.Frame(self.root)
        self.tv_top = ttk.Treeview(frame_top, columns=ac, show='headings', height=7)
        setup_headers(ac, self.tv_top, column_labels, column_widths)

        verscrlbar1 = ttk.Scrollbar(frame_top, orient="vertical", command=self.tv_top.yview)
        verscrlbar1.pack(side='right', fill='both')

        self.tv_top.pack()
        self.tv_top.bind('<Double-1>', self.go_to_freq)  # double-click
        self.tv_top.bind('<Double-3>', self.on_worked)  # double-right-click
        self.tv_top.configure(yscrollcommand=verscrlbar1.set)

        frame_top.pack()

        def on_mode_click():
            settings.save_mode_filters(self.mode_filters)

        frame_options = tk.Frame(self.root)
        self.mode_filters = {}
        for mode_filter in helpers.ModeFilter:
            self.mode_filters[mode_filter.value] = tk.BooleanVar(value=(mode_filter in self.settings.mode_filters))
            tk.Checkbutton(frame_options, text=mode_filter.value, variable=self.mode_filters[mode_filter.value],
                           command=on_mode_click).pack(side='left')
        frame_options.pack()

        tk.Button(self.root, text="Refresh", command=self.do_refresh_query).pack()

        interval_frame = tk.Frame(self.root)
        tk.Label(interval_frame, text='Interval (mins)').pack(side='left')
        self.interval_val = tk.StringVar(value=settings.refresh_interval)
        tk.Entry(interval_frame, textvariable=self.interval_val, width=3).pack(side='left')
        interval_frame.pack()

        max_age_frame = tk.Frame(self.root)
        tk.Label(max_age_frame, text='Max age (mins)').pack(side='left')
        self.max_age_val = tk.StringVar(value=settings.max_age)
        tk.Entry(max_age_frame, textvariable=self.max_age_val, width=3).pack(side='left')
        max_age_frame.pack()

        tk.Label(self.root).pack()  # spacing
        tk.Label(self.root, text='Worked spots today').pack()

        frame_bottom = tk.Frame(self.root)
        self.tv_bottom = ttk.Treeview(frame_bottom, columns=ac, show='headings', height=7)
        setup_headers(ac, self.tv_bottom, column_labels, column_widths)

        verscrlbar2 = ttk.Scrollbar(frame_bottom, orient="vertical", command=self.tv_bottom.yview)
        verscrlbar2.pack(side='right', fill='both')

        self.tv_bottom.pack()
        self.tv_bottom.bind('<Double-1>', self.go_to_freq)
        self.tv_bottom.bind('<Double-3>', self.move_to_top_table)
        self.tv_top.configure(yscrollcommand=verscrlbar1.set)

        frame_bottom.pack()

        self.last_updated_var = tk.StringVar(value="Last updated:")
        tk.Label(self.root, textvariable=self.last_updated_var).pack()

        self.feedback_var = tk.StringVar(value="")
        self.feedback_label = tk.Label(self.root, textvariable=self.feedback_var)
        self.feedback_label.pack()

        self.root.protocol("WM_DELETE_WINDOW", self.cleanup)
        self.lookups_and_fill_grid()

        self.next_query = self.root.after(self.get_poll_interval_ms(), self.do_refresh_query)

        self.root.mainloop()

    def do_refresh_query(self):
        self.settings.save_other_preferences(self.get_poll_interval_ms(), self.get_max_age())
        self.feedback("Doing query...")
        self.root.after_cancel(self.next_query)
        self.lookups_and_fill_grid()
        self.next_query = self.root.after(self.get_poll_interval_ms(), self.do_refresh_query)
        print("Next refresh is in", self.get_poll_interval_ms(), "ms")

    def get_poll_interval_ms(self):
        MS_IN_MIN = 60000
        try:
            interval = abs(float(self.interval_val.get()))
            return int(interval * MS_IN_MIN)
        except ValueError:
            print("Invalid interval_val, defaulting to 1 min")
            return 1 * MS_IN_MIN

    def get_max_age(self) -> int:
        try:
            return abs(int(self.max_age_val.get()))
        except ValueError:
            print("Invalid max_age_val, defaulting to", self.settings.max_age)
            return self.settings.max_age

    def show_last_updated(self, successful):
        status = "Updated" if successful else "Error"
        self.last_updated_var.set(status + " at " + time.strftime("%H:%M:%S"))

    def feedback(self, text):
        print(text)
        self.feedback_var.set(text)
        self.feedback_label.update()

    def get_mode_filters(self) -> List[helpers.ModeFilter]:
        mode_filters = []
        for mode_filter in helpers.ModeFilter:
            if self.mode_filters[mode_filter.value].get():
                mode_filters.append(mode_filter)
        return mode_filters

    def lookups_and_fill_grid(self):
        query_spots, query_errors = self.data_fetcher.retrieve_filtered_spots_by_time(spot_limit=MAX_SPOTS_QUERY,
                                                                                      time_limit=self.get_max_age())

        self.top_spots = query_spots.copy()

        # remove older entries for same call
        for spot1 in self.top_spots.copy():
            for spot2 in self.top_spots.copy():
                if spot1 != spot2 and spot1.callsign == spot2.callsign:
                    # special case where it's a POTA+SOTA activation
                    if SHOW_SPOTA_TWICE and spot1.activation_type != spot2.activation_type:
                        # when flag is true, spots are considered different types so don't need to eliminate one
                        continue

                    if spot_age_mins(spot1) > spot_age_mins(spot2):
                        print("removing older spot from same call", "spot1:", spot1.to_string(), "spot2:",
                              spot2.to_string())
                        if spot1 in self.top_spots:
                            self.top_spots.remove(spot1)
                    elif spot_age_mins(spot1) == spot_age_mins(spot2):
                        if spot1.frequency == spot2.frequency:
                            if spot1 in self.top_spots:
                                self.top_spots.remove(spot1)
                        else:
                            # just keep both around in this case
                            pass

        # remove outdated entries from worked_spots (after a new UTC day)
        for worked in self.worked_spots.copy():
            if not worked.worked_today():
                self.worked_spots.remove(worked)

        # remove worked ones from result
        for spot in self.top_spots.copy():
            for worked in self.worked_spots.copy():
                if matches_worked(spot, worked) and spot in self.top_spots:  # could have already been removed
                    self.top_spots.remove(spot)

        # remove wrong mode (filter these last so that we'll know if a spot was abandoned for another mode)
        for top in self.top_spots.copy():
            if not helpers.in_mode_filters(top.mode, self.get_mode_filters()):
                self.top_spots.remove(top)

        fill_treeview(self.tv_top, self.top_spots)
        fill_treeview(self.tv_bottom, self.worked_spots)

        if query_errors:
            self.feedback("Problem querying API!" + '\n' + str([err.args[0] for err in query_errors]))
            self.show_last_updated(False)
        else:
            self.feedback("Finished lookup")
            self.show_last_updated(True)

    # https://stackoverflow.com/a/25217053
    def highlight_right_clicked(self, tv, event):
        # select row under mouse
        iid = tv.identify_row(event.y)
        if iid:
            # mouse pointer over item
            if len(self.tv_top.selection()) > 0:
                self.tv_top.selection_remove(self.tv_top.selection()[0])
            if len(self.tv_bottom.selection()) > 0:
                self.tv_bottom.selection_remove(self.tv_bottom.selection()[0])
            tv.selection_set(iid)
            # self.contextMenu.post(event.x_root, event.y_root)
        else:
            # mouse pointer not over item
            # occurs when items do not fill frame
            # no action required
            pass

    def move_from_to(self, from_tv, event, from_spots, to_spots, moving_down):
        self.highlight_right_clicked(from_tv, event)
        item = from_tv.selection()[0]
        vals = from_tv.item(item, 'values')
        self.feedback("Moving " + vals[1])
        row_index = int(item)
        to_move = from_spots[row_index]
        if moving_down:
            to_move.worked_day = helpers.get_yyyymmdd_now()
        else:
            to_move.worked_day = ''
        to_spots.append(to_move)
        from_spots.remove(to_move)
        fill_treeview(self.tv_top, self.top_spots)
        fill_treeview(self.tv_bottom, self.worked_spots)
        self.feedback("Moved " + vals[1])

    def on_worked(self, event):
        self.move_from_to(self.tv_top, event, self.top_spots, self.worked_spots, True)
        worked_history.save_worked_history(self.worked_spots)

    def move_to_top_table(self, event):
        self.move_from_to(self.tv_bottom, event, self.worked_spots, self.top_spots, False)
        worked_history.save_worked_history(self.worked_spots)

    def go_to_freq(self, event):
        item = event.widget.selection()[0]
        vals = event.widget.item(item, 'values')
        print("Event on", vals)
        freq_mhz = vals[3]
        freq_hz = int(float(freq_mhz) * 1000000)
        self.feedback("Setting freq to " + str(freq_mhz))
        set_vfo_result = self.rig_control.set_vfo(freq_hz)
        if set_vfo_result.success:
            self.feedback("Freq was set to " + str(freq_mhz))
        elif set_vfo_result.error_msg:
            self.feedback("Freq not set: " + set_vfo_result.error_msg)
        else:  # unknown if it changed
            self.feedback("")

    def cleanup(self):
        print("cleanup")
        self.rig_control.cleanup_rig()
        self.root.destroy()


if __name__ == '__main__':
    my_settings = Settings()
    my_rig = Rig.rig_factory(RIG_CONFIG_FILE)
    if my_rig:
        ScannerView(my_settings, my_rig)
    else:
        print("Problem with rig configuration in", RIG_CONFIG_FILE)
