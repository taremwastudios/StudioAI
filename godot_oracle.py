import os
import sqlite3
from datetime import datetime

class GodotOracle:
    def __init__(self, db_path="/home/Taremwastudios/TaremwaStudios/matrix_mel.db"):
        self.db_path = db_path
        self._init_oracle()

    def _init_oracle(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("CREATE TABLE IF NOT EXISTS godot_patterns (id INTEGER PRIMARY KEY, type TEXT, pattern_name TEXT, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
        conn.commit()
        conn.close()

    def index_pattern(self, pattern_type, name, content):
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO godot_patterns (type, pattern_name, content) VALUES (?, ?, ?)",
                     (pattern_type, name, content))
        conn.commit()
        conn.close()
        print(f"Oracle: Indexed {pattern_type} pattern - {name}")

    def get_template(self, pattern_name):
        conn = sqlite3.connect(self.db_path)
        res = conn.execute("SELECT content FROM godot_patterns WHERE pattern_name = ?", (pattern_name,)).fetchone()
        conn.close()
        return res[0] if res else None

# Pre-populating the Oracle with Foundation Patterns
oracle = GodotOracle()
# 2D Character Template
GD_PLAYER_SCRIPT = """
extends CharacterBody2D
const SPEED = 300.0
func _physics_process(delta):
    var direction = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
    if direction:
        velocity = direction * SPEED
    else:
        velocity.x = move_toward(velocity.x, 0, SPEED)
        velocity.y = move_toward(velocity.y, 0, SPEED)
    move_and_slide()
"""
# Foundation for project.godot
PROJECT_GODOT_TEMPLATE = """
config_version=5
[application]
config/name="{game_name}"
run/main_scene="res://scenes/Main.tscn"
config/features=PackedStringArray("4.2", "Forward Plus")
[display]
window/size/viewport_width=1152
window/size/viewport_height=648
[rendering]
renderer/rendering_method="mobile"
"""

# Foundation for export_presets.cfg
EXPORT_PRESETS_TEMPLATE = """
[preset.0]
name="Android"
platform="Android"
runnable=true
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="{export_path}"
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false

[preset.0.options]
custom_template/debug=""
custom_template/release=""
graphics/driver="Forward Plus"
package/unique_name="com.taremwa.{game_name_safe}"
package/name="{game_name}"
package/signed=true
package/classification="Games"
launcher_icons/main_192x192=""
launcher_icons/adaptive_foreground_432x432=""
launcher_icons/adaptive_background_432x432=""
keystore/debug="/home/Taremwastudios/.android/debug.keystore"
keystore/debug_user="androiddebugkey"
keystore/debug_password="android"
keystore/release=""
keystore/release_user=""
keystore/release_password=""
version/code=1
version/name="1.0"
apk/alignment=0
architectures/armeabi-v7a=true
architectures/arm64-v8a=true
architectures/x86=false
architectures/x86_64=false
permissions/custom_permissions=PackedStringArray()
"""

# Foundation for a basic 2D Scene
TSCN_2D_FOUNDATION = """
[gd_scene load_steps=1 format=3]
[node name="Main" type="Node2D"]
"""

oracle.index_pattern("config", "base_project", PROJECT_GODOT_TEMPLATE)
oracle.index_pattern("config", "export_presets", EXPORT_PRESETS_TEMPLATE)
oracle.index_pattern("scene", "base_2d", TSCN_2D_FOUNDATION)
