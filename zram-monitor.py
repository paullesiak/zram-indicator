#!/usr/bin/env python
#
# ZRAM usage appindicator
#
# Author: Paul Lesiak
# Email: paul@paullesiak.com
# URL: github.com/paullesiak/zram-indicator
#
# References:
#    https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-block-zram
#
import os
import psutil
import sys
import locale

gtk = True
try:
    from gi.repository import Gtk, GLib
    from gi.repository import AppIndicator3 as appindicator
except ImportError:
    gtk = False

locale.setlocale(locale.LC_ALL, 'en_US.UTF8')

def sizeof_fmt(num):
    # http://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size
    for x in ['bytes', 'KB', 'MB', 'GB']:
        if num < 1024.0 and num > -1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')


class ZramUsage(object):

    blockpath = '/sys/block'

    def blocks(self):
        return [z for z in os.listdir(self.blockpath) if z.startswith('zram')]

    def readzramstats(self, statfile):
        data = 0
        for block in self.blocks():
            f = os.path.join(self.blockpath, block, statfile)
            if os.path.exists(f):
                with open(f, 'r') as handle:
                    data += int(handle.read())

        return data

    def numberofblocks(self, pretty=False):
        stat = len(self.blocks())
        if pretty:
            return 'Number of zRam devices: {0}'.format(stat)
        return stat

    def compresseddatasize(self, pretty=False):
        stat = self.readzramstats('compr_data_size')
        if pretty:
            return 'Compressed Data Size: {0}'.format(sizeof_fmt(stat))
        return stat

    def originaldatasize(self, pretty=False):
        stat = self.readzramstats('orig_data_size')
        if pretty:
            return 'Uncompressed Data Size: {0}'.format(sizeof_fmt(stat))
        return stat

    def memusedtotal(self, pretty=False):
        stat = self.readzramstats('mem_used_total')
        if pretty:
            return 'Total zRam Memory Usage: {0}'.format(sizeof_fmt(stat))
        return stat

    def disksize(self, pretty=False):
        stat = self.readzramstats('disksize')
        if pretty:
            return 'Total uncompressed capacity: {0}'.format(sizeof_fmt(stat))
        return stat

    def notifyfree(self, pretty=False):
        stat = self.readzramstats('disksize')
        if pretty:
            return 'Swap slot free notifies: {0}'.format(locale.format('%d', stat, grouping=True))
        return stat

    def readcount(self, pretty=False):
        stat = self.readzramstats('num_reads')
        if pretty:
            return 'Number of reads: {0}'.format(locale.format('%d', stat, grouping=True))
        return stat

    def writecount(self, pretty=False):
        stat = self.readzramstats('num_reads')
        if pretty:
            return 'Number of writes: {0}'.format(locale.format('%d', stat, grouping=True))
        return stat

    def zeropages(self, pretty=False):
        stat = self.readzramstats('zero_pages')
        if pretty:
            return 'Unallocated pages: {0}'.format(locale.format('%d', stat, grouping=True))
        return stat

    def size(self, pretty=False):
        stat = self.readzramstats('size')
        if pretty:
            return 'Size?: {0}'.format(sizeof_fmt(stat))
        return stat

    def compressionratio(self, pretty=False):
        stat = 1.0 - \
            (float(self.compresseddatasize()) / float(self.originaldatasize()))
        if pretty:
            return 'Compression Ratio: {0:.2f}%'.format(stat * 100.0)
        return stat

    def zramutilization(self, pretty=False):
        stat = 1.0 - (float(self.originaldatasize()) / float(self.swapusage()))
        if pretty:
            return 'zRam Utilization Ratio: {0:.2f}%'.format(stat * 100.0)
        return stat

    def swapusage(self, pretty=False):
        swap = psutil.swap_memory()
        stat = swap.used
        if pretty:
            return 'Swap Usage: {0}'.format(sizeof_fmt(stat))
        return stat

    def __repr__(self):

        output = ''
        cmdList = [
            zram.compressionratio, 
            zram.zramutilization,
            zram.numberofblocks, 
            zram.compresseddatasize, 
            zram.originaldatasize, 
            zram.memusedtotal, 
            zram.swapusage, 
            zram.disksize, 
            zram.readcount,
            zram.writecount,
            zram.zeropages,
            zram.notifyfree, 
        ]

        for s in cmdList:
            output += '{0}\n'.format(s(True))

        return output

if gtk:
    png = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'zram.png')
    zram = ZramUsage()

    cmdList = [
        zram.compressionratio, 
        zram.zramutilization,
        zram.numberofblocks, 
        zram.compresseddatasize, 
        zram.originaldatasize, 
        zram.memusedtotal, 
        zram.swapusage, 
        zram.disksize, 
        zram.readcount,
        zram.writecount,
        zram.zeropages,
        zram.notifyfree, 
    ]
    menuItems = []

    def appindicator_exit(w, data):
        Gtk.main_quit()

    def appindicator_readzram(ind_app, menu, firstRun=False):

        stat = zram.compressionratio(pretty=False)

        ind_app.set_label('{0:.2f}%'.format(stat * 100.0), '')

        # if not firstRun:
        #     menu = ind_app.get_menu()

        for i, s in enumerate(cmdList):
            if firstRun:
                menu_item = Gtk.MenuItem(s(True))
                menu.append(menu_item)
                menu_item.show()
                menuItems.append(menu_item)
            else:
                menu_item = menuItems[i]
                menu_item.set_label(s(True))

        return 1

    ind_app = appindicator.Indicator.new_with_path(
        "zram-indicator",
        png,
        appindicator.IndicatorCategory.APPLICATION_STATUS,
        os.path.dirname(os.path.realpath(__file__)))

    ind_app.set_status(appindicator.IndicatorStatus.ACTIVE)

    # create a menu
    menu = Gtk.Menu()
    appindicator_readzram(ind_app, menu, firstRun=True)

    menu_items = Gtk.MenuItem("Exit")
    menu.append(menu_items)
    menu_items.connect("activate", appindicator_exit, '')
    menu_items.show()

    ind_app.set_menu(menu)

    GLib.timeout_add(1000, appindicator_readzram, ind_app, False)
    Gtk.main()
else:
    print str(ZramUsage())
