
import os
from knowledge_manager import KnowledgeManager

def populate_knowledge():
    km = KnowledgeManager()
    
    # Ingest STUDIO_PROFILE.md
    profile_path = "../STUDIO_PROFILE.md"
    if os.path.exists(profile_path):
        with open(profile_path, "r") as f:
            content = f.read()
            km.add_entry(
                topic="Taremwa Studios Profile",
                content=content,
                tags="studio, history, philosophy, portfolio",
                source="STUDIO_PROFILE.md"
            )
            print("Ingested STUDIO_PROFILE.md")

    # Ingest rpg_game/game_manual.md
    manual_path = "../rpg_game/game_manual.md"
    if os.path.exists(manual_path):
        with open(manual_path, "r") as f:
            content = f.read()
            km.add_entry(
                topic="RPG Game Manual",
                content=content,
                tags="rpg, mechanics, levels, stats, clans, economy",
                source="game_manual.md"
            )
            print("Ingested game_manual.md")

    # Add some specific entries for GamiCore
    km.add_entry(
        topic="GamiCore Engine",
        content="GamiCore is a high-performance C++ ECS (Entity Component System) game engine with Python bindings. It focuses on Data-Oriented Design (DOD) and zero-cost abstractions.",
        tags="engine, gamicore, c++, ecs, dod",
        source="internal"
    )
    print("Added GamiCore entry")

    # Add entry for Hero's Odyssey
    km.add_entry(
        topic="Hero's Odyssey",
        content="Hero's Odyssey is the flagship title of Taremwa Studios. It is an immersive RPG with deep mechanics and world-building. A 'Full Edition' also exists with enhanced systems.",
        tags="game, hero, odyssey, rpg",
        source="internal"
    )
    print("Added Hero's Odyssey entry")

if __name__ == "__main__":
    populate_knowledge()
