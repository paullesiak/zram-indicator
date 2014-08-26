#!/usr/bin/env python

import os
import psutil
import sys
from gi.repository import Gtk, GLib
from gi.repository import AppIndicator3 as appindicator


def sizeof_fmt(num):
    for x in ['bytes', 'KB', 'MB', 'GB']:
        if num < 1024.0 and num > -1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')


class ZramUsage(object):

    def getzramusage(self):
        blockpath = '/sys/block'
        statfiles = [
            'compr_data_size', 'orig_data_size', 'mem_used_total',
            'disksize', 'notify_free', 'size', 'zero_pages']

        zramblocks = [z for z in os.listdir(blockpath) if z.startswith('zram')]
        stats = dict((k, 0) for k in statfiles)
        for block in zramblocks:
            for statfile in statfiles:
                f = os.path.join(blockpath, block, statfile)
                if os.path.exists(f):
                    data = 0
                    sumdata = stats.get(statfile, 0)
                    with open(f, 'r') as handle:
                        data = handle.read()
                    # print '{0} = {1}'.format(f, sizeof_fmt(int(data)))
                    stats[statfile] = sumdata + int(data)
        percentage = 100 * \
            float(stats[statfiles[0]]) / float(stats[statfiles[1]])
        stats['percent'] = percentage
        stats['blocks'] = zramblocks
        return stats

    def __repr__(self):

        output = ''
        stats = self.getzramusage()

        swap = psutil.swap_memory()

        output += 'swap in use: {0}\n'.format(sizeof_fmt(swap.used))
        output += 'number of zram devices: {0}\n'.format(len(stats['blocks']))
        for k in ['compr_data_size', 'orig_data_size',
                  'mem_used_total', 'disksize']:
            output += '{0}: {1}\n'.format(k, sizeof_fmt(stats.get(k)))
        output += 'zram compressed size: {0:.2f}%\n'.format(stats['percent'])

        return output

png = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'zram.png')


def cb_exit(w, data):
    Gtk.main_quit()


def cb_readzram(ind_app):
    stats = ZramUsage().getzramusage()
    compressed = 100 - float(stats['percent'])
    output = 'ZRAM: {0:.2f}%, {1}/{2}'.format(
        compressed, sizeof_fmt(stats['compr_data_size']), sizeof_fmt(stats['orig_data_size']))
    ind_app.set_label(output, '')
    return 1

ind_app = appindicator.Indicator.new_with_path(
    "zram-indicator",
    png,
    appindicator.IndicatorCategory.APPLICATION_STATUS,
    os.path.dirname(os.path.realpath(__file__)))
ind_app.set_status(appindicator.IndicatorStatus.ACTIVE)

# create a menu
menu = Gtk.Menu()
menu_items = Gtk.MenuItem("Exit")
menu.append(menu_items)
menu_items.connect("activate", cb_exit, '')
menu_items.show()
ind_app.set_menu(menu)
GLib.timeout_add(1000, cb_readzram, ind_app)
Gtk.main()
