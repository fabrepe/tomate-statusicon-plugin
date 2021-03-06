from __future__ import unicode_literals

import logging

import tomate.plugin
from gi.repository import Gtk
from tomate.constant import State
from tomate.event import connect_events, disconnect_events, Events, on
from tomate.graph import graph
from tomate.utils import rounded_percent, suppress_errors
from tomate.view import TrayIcon
from wiring import implements

logger = logging.getLogger(__name__)


@implements(TrayIcon)
class StatusIconPlugin(tomate.plugin.Plugin):
    @suppress_errors
    def __init__(self):
        super(StatusIconPlugin, self).__init__()

        self.menu = graph.get('trayicon.menu')
        self.session = graph.get('tomate.session')
        self.widget = self.new_status_icon()

    @suppress_errors
    def activate(self):
        super(StatusIconPlugin, self).activate()

        graph.register_instance(TrayIcon, self)
        connect_events(self.menu)

        self._show_if_session_is_running()

    @suppress_errors
    def deactivate(self):
        super(StatusIconPlugin, self).deactivate()

        graph.unregister_provider(TrayIcon)
        disconnect_events(self.menu)

        self.hide()

    @suppress_errors
    @on(Events.Session, [State.started])
    def show(self, sener=None, **kwargs):
        self.widget.set_visible(True)

        logger.debug('Plugin status icon is showing')

    @suppress_errors
    @on(Events.Session, [State.finished, State.stopped])
    def hide(self, sender=None, **kwargs):
        self.widget.set_visible(False)
        self.widget.set_from_icon_name('tomate-idle')

        logger.debug('Plugin status icon is hiding')

    @suppress_errors
    @on(Events.Timer, [State.changed])
    def update_icon(self, sender=None, **kwargs):
        percent = int(kwargs.get('time_ratio', 0) * 100)

        if rounded_percent(percent) < 99:
            icon_name = self._icon_name_for(percent)
            self.widget.set_from_icon_name(icon_name)

            logger.debug('set icon %s', icon_name)
            
    @suppress_errors
    @on(Events.Session, [State.started])
    def auto_hide_view(self, sender=None, **kwargs):
        self.menu._on_hide_item_activate(None)
        logger.debug("Automatically hide view")

    def new_status_icon(self):
        widget = Gtk.StatusIcon(visible=False)
        widget.set_from_icon_name('tomate-idle')
        widget.set_title("StatusIcon")
        widget.connect("button-press-event", self._popup_menu)
        widget.connect("popup-menu", self._popup_menu)

        return widget

    def _popup_menu(self, statusicon, event_or_button, active_time=None):
        self.menu.widget.popup(None, None, None, None, 0, Gtk.get_current_event_time())

    @staticmethod
    def _icon_name_for(percent):
        return 'tomate-{0:02}'.format(rounded_percent(percent))

    def _show_if_session_is_running(self):
        if self.session.is_running():
            self.show()

        else:
            self.hide()
