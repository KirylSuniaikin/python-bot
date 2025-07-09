from flask import current_app

from app.repositories.repository import get_menu_items, get_extra_ingr

def load_menu_cache():
    items = get_menu_items()
    current_app.menu_cache = [item.to_dict() for item in items]
    print("Menu cache loaded. Items:", len(current_app.menu_cache))

def load_extra_ingr_cache():
    ingr = get_extra_ingr()
    current_app.extra_ingr_cache = [i.to_dict() for i in ingr]
    print("Extra ingr cache loaded. Items:", len(current_app.extra_ingr_cache))