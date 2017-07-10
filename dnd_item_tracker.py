from asciimatics.widgets import Frame, ListBox, Layout, Divider, Text, \
    Button, TextBox, Widget
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
import sys
import sqlite3
import json

class itemModel(object):
    def __init__(self):
        # Create a database in RAM
        self._db = sqlite3.connect('items.db')
        self._db.row_factory = sqlite3.Row

        # Create the basic contact table.
        self._db.cursor().execute('''
            CREATE TABLE if not exists weapons(
                id INTEGER PRIMARY KEY,
                name TEXT,
                weight TEXT,
                modifiers TEXT,
                damage TEXT,
                range TEXT,
                damageType TEXT,
                price TEXT,
                rarity TEXT,
                properties TEXT,
                description TEXT
                )
        ''')
        self._db.commit()
        self.current_id = None

    def add(self, weapon):
        self._db.cursor().execute('''
            INSERT INTO weapons(name, weight, modifiers, damage, range, damageType, price, rarity, properties, description)
            VALUES(:name, :weight, :modifiers, :damage, :range, :damageType, :price, :rarity, :properties, :description)''', weapon)

        self._db.commit()

    def get_summary(self):
        return self._db.cursor().execute(
            "SELECT name, id FROM weapons").fetchall()

    def get_weapon(self, weapon_id):
        return self._db.cursor().execute(
            "SELECT * FROM weapons where id=:id", {"id": weapon_id}).fetchone()

    def get_current_weapon(self):
        if self.current_id is None:
            return {}
        else:
            return self.get_weapon(self.current_id)

    def export_items(self):
        return self._db.cursor().execute("SELECT * FROM weapons").fetchall()


    def update_current_weapon(self, details):
        if self.current_id is None:
            self.add(details)
        else:
            self._db.cursor().execute('''
                UPDATE weapons SET name=:name, weight=:weight, modifiers=:modifiers, damage=:damage, range=:range,
                damageType=:damageType, price=:price, rarity=:rarity, properties=:properties, description=:description
                WHERE id=:id''', details)

            self._db.commit()

    def delete_weapon(self, weapon_id):
        self._db.cursor().execute('''
            DELETE FROM weapons WHERE id=:id''', {"id": weapon_id})
        self._db.commit()

class ListView(Frame):
    def __init__(self, screen, model):
        super(ListView, self).__init__(screen,
                                       screen.height * 2 // 3,
                                       screen.width * 2 // 3,
                                       on_load=self._reload_list,
                                       hover_focus=False,
                                       title="Item List")

        self._model = model

        # Create the form for displaying the list of contacts.
        self._list_view = ListBox(
            Widget.FILL_FRAME,
            model.get_summary(),
            name="weapons",
            on_change=self._on_pick)
        self._edit_button = Button("Edit", self._edit)
        self._delete_button = Button("Delete", self._delete)
        self._export_button = Button("Export", self._export)
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(self._list_view)
        layout.add_widget(Divider())
        layout2 = Layout([1, 1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Add", self._add), 0)
        layout2.add_widget(self._edit_button, 1)
        layout2.add_widget(self._export_button, 2)
        layout2.add_widget(self._delete_button, 3)
        layout2.add_widget(Button("Quit", self._quit), 4)
        self.fix()
        self._on_pick()

    def _on_pick(self):
        self._edit_button.disabled = self._list_view.value is None
        self._delete_button.disabled = self._list_view.value is None
        self._export_button.disabled = self._list_view.value is None

    def _reload_list(self):
        self._list_view.options = self._model.get_summary()
        self._model.current_id = None

    def _add(self):
        self._model.current_id = None
        raise NextScene("Edit Contact")

    def _export(self):
        all_items = self._model.export_items()
        items_json = json.dumps([dict(ix) for ix in all_items])
        with open('items.json', 'w') as f:
            f.write(items_json)
        data = json.loads(items_json)
        with open('readable_items.txt', 'w') as f:
            for item in data:
                f.write('-----------------------------------------\n')
                f.write('Name: ' + item['name'] + '\n')
                f.write('Weight: ' + item['weight'] + '\n')
                f.write('Range: ' + item['range'] + '\n')
                f.write('Modifiers: ' + item['modifiers'] + '\n')
                f.write('Damage: ' + item['damage'] + '\n')
                f.write('Damage Type: ' + item['damageType'] + '\n')
                f.write('Price: ' + item['price'] + '\n')
                f.write('Rarity: ' + item['rarity'] + '\n')
                f.write('Properties: ' + item['properties'] + '\n')
                f.write('Description:\n| ' + item['description'].replace('  ', '\t').replace('\n', '\n| ') + '\n')

    def _edit(self):
        self.save()
        self._model.current_id = self.data["weapons"]
        raise NextScene("Edit Contact")

    def _delete(self):
        self.save()
        self._model.delete_weapon(self.data["weapons"])
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
                                          title="Item details",
                                          reduce_cpu=True)
        # Save off the model that accesses the contacts database.
        self._model = model

        # Create the form for displaying the list of contacts.
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(Text("Name:", "name"))
        layout.add_widget(Text("Weight:", "weight"))
        layout.add_widget(Text("Modifiers:", "modifiers"))
        layout.add_widget(Text("Range:", "range"))
        layout.add_widget(Text("Damage:", "damage"))
        layout.add_widget(Text("Damage Type:", "damageType"))
        layout.add_widget(Text("Price:", "price"))
        layout.add_widget(Text("Rarity:", "rarity"))
        layout.add_widget(Text("Properties:", "properties"))
        layout.add_widget(TextBox(
            Widget.FILL_FRAME, "Description:", "description", as_string=True))
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
