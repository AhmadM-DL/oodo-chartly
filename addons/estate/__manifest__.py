{
    "name": "Estate Management",
    "version": "1.0",
    "category": "Real Estate",
    "summary": "Manage real estate properties, agents, and clients.",
    "description": "This module provides functionalities to manage real estate properties, agents, and clients. It includes features for property listings, agent assignments, and client interactions.",
    "author": "Ahmad Mustapha",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "views/property_views.xml",
        "views/property_type_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}