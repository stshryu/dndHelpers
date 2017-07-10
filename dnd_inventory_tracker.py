from asciimatics.widgets import Frame, ListBox, Layout, Divider, Text, \
    Button, TextBox, Widget
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
import sys
import sqlite3

class itemModel(object):
    def __init__(self):
        # Create a database in RAM
        self._db = sqlite3.connect('items.db')
        self._db.row_factory = sqlite3.Row

        # Create the basic contact table.
        self._db.cursor().execute('''
            CREATE TABLE if not exists inventory(
                id INTEGER PRIMARY KEY,
                name TEXT,
                price TEXT,
                charges TEXT,
                quantity TEXT
                )
        ''')
        self._db.commit()
        self.current_id = None

    def add(self, item):
        self._db.cursor().execute('''
            INSERT INTO inventory(name, price, charges, quantity)
            VALUES(:name, :price, :charges, :quantity)''', item)

        self._db.commit()

    def get_summary(self):
        return self._db.cursor().execute(
            "SELECT name || ' -- ' || quantity, id FROM inventory").fetchall()

    def get_weapon(self, weapon_id):
        return self._db.cursor().execute(
            "SELECT * FROM inventory WHERE id=:id", {"id": weapon_id}).fetchone()

    def increase_quantity(self, weapon_id):
        self._db.cursor().execute("UPDATE inventory SET quantity = quantity + 1 WHERE id=:id", {"id": weapon_id})
        self._db.commit()

    def decrease_quantity(self, weapon_id):
        self._db.cursor().execute("UPDATE inventory SET quantity = quantity - 1 WHERE id=:id", {"id": weapon_id})
        self._db.commit()

    def get_current_weapon(self):
        if self.current_id is None:
            return {}
        else:
            return self.get_weapon(self.current_id)

    def get_current_weapon_id(self):
        if self.current_id is None:
            return {}
        else:
            return int(self.current_id)

    def update_current_weapon(self, details):
        if self.current_id is None:
            self.add(details)
        else:
            self._db.cursor().execute('''
                UPDATE inventory SET name=:name, price=:price, charges=:charges, quantity=:quantity
                WHERE id=:id''', details)

            self._db.commit()

    def delete_weapon(self, weapon_id):
        self._db.cursor().execute('''
            DELETE FROM inventory WHERE id=:id''', {"id": weapon_id})
        self._db.commit()

class ListView(Frame):
    def __init__(self, screen, model):
        super(ListView, self).__init__(screen,
                                       screen.height * 2 // 3,
                                       screen.width * 2 // 3,
                                       on_load=self._reload_list,
                                       hover_focus=False,
                                       title="Inventory")
        self._model = model

        # Create the form for displaying the list of contacts.
        self._list_view = ListBox(
            Widget.FILL_FRAME,
            model.get_summary(),
            name="inventory",
            on_change=self._on_pick)
        self._edit_button = Button("Edit", self._edit)
        self._delete_button = Button("Delete", self._delete)
        self._increment_button = Button("+1", self._increment)
        self._decrement_button = Button("-1", self._decrement)
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(self._list_view)
        layout.add_widget(Divider())
        layout2 = Layout([1, 1, 1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Add", self._add), 0)
        layout2.add_widget(self._edit_button, 1)
        layout2.add_widget(self._increment_button, 2)
        layout2.add_widget(self._decrement_button, 3)
        layout2.add_widget(self._delete_button, 4)
        layout2.add_widget(Button("Quit", self._quit), 5)
        self.fix()
        self._on_pick()

    def _on_pick(self):
        self._edit_button.disabled = self._list_view.value is None
        self._delete_button.disabled = self._list_view.value is None
        self._increment_button.disabled = self._list_view.value is None
        self._decrement_button.disabled = self._list_view.value is None

    def _reload_list(self, keep_selected=None):
        self._list_view.options = self._model.get_summary()
        if keep_selected is not None:
            self._model.current_id = keep_selected
        else:
            self._model.current_id = None

    def _add(self):
        self._model.current_id = None
        raise NextScene("Edit Contact")

    def _increment(self):
        self.save()
        self._model.increase_quantity(self.data["inventory"])
        self._reload_list(self.data["inventory"])

    def _decrement(self):
        self.save()
        self._model.decrease_quantity(self.data["inventory"])
        self._reload_list(self.data["inventory"])

    def _edit(self):
        self.save()
        self._model.current_id = self.data["inventory"]
        raise NextScene("Edit Contact")

    def _delete(self):
        self.save()
        self._model.delete_weapon(self.data["inventory"])
        self._reload_list()

    @staticmethod
    def _quit():
        raise StopApplication("User pressed quit")

class ContactView(Frame):
    def __init__(self, screen, model):
        super(ContactView, self).__init__(screen,
                                          screen.height * 2 // 3,
                                          screen.width * 2 // 3,
                                          hover_focus=False,
                                          title="Item Details",
                                          reduce_cpu=True)
        # Save off the model that accesses the contacts database.
        self._model = model

        # Create the form for displaying the list of contacts.
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(Text("Name:", "name"))
        layout.add_widget(Text("Price:", "price"))
        layout.add_widget(Text("Charges:","charges"))
        layout.add_widget(Text("Quantity:", "quantity"))
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("OK", self._ok), 0)
        layout2.add_widget(Button("Cancel", self._cancel), 3)
        self.fix()

    def reset(self):
        # Do standard reset to clear out form, then populate with new data.
        super(ContactView, self).reset()
        self.data = self._model.get_current_weapon()

    def _ok(self):
        self.save()
        self._model.update_current_weapon(self.data)
        raise NextScene("Main")

    @staticmethod
    def _cancel():
        raise NextScene("Main")


def demo(screen, scene):
    scenes = [
        Scene([ListView(screen, contacts)], -1, name="Main"),
        Scene([ContactView(screen, contacts)], -1, name="Edit Contact")
    ]

    screen.play(scenes, stop_on_resize=True, start_scene=scene)

contacts = itemModel()
last_scene = None
while True:
    try:
        Screen.wrapper(demo, catch_interrupt=True, arguments=[last_scene])
        sys.exit(0)
    except ResizeScreenError as e:
        last_scene = e.scene
