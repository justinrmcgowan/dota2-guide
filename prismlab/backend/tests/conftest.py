import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from data.database import Base, get_db
from data.models import Hero, Item, HeroAbilityData, ItemTimingData
from main import app


test_engine = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
)
test_async_session = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def test_db_setup():
    """Create tables and seed test data."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_async_session() as session:
        # Seed test heroes
        heroes = [
            Hero(
                id=1,
                name="Anti-Mage",
                localized_name="Anti-Mage",
                internal_name="npc_dota_hero_antimage",
                primary_attr="agi",
                attack_type="Melee",
                roles=["Carry", "Escape"],
            ),
            Hero(
                id=2,
                name="Axe",
                localized_name="Axe",
                internal_name="npc_dota_hero_axe",
                primary_attr="str",
                attack_type="Melee",
                roles=["Initiator", "Durable"],
            ),
            Hero(
                id=3,
                name="Crystal Maiden",
                localized_name="Crystal Maiden",
                internal_name="npc_dota_hero_crystal_maiden",
                primary_attr="int",
                attack_type="Ranged",
                roles=["Support", "Nuker"],
            ),
        ]
        session.add_all(heroes)

        # Additional heroes used by rules engine tests
        extra_heroes = [
            Hero(
                id=22, name="Zeus", localized_name="Zeus",
                internal_name="npc_dota_hero_zuus",
                primary_attr="int", attack_type="Ranged",
                roles=["Nuker", "Carry"],
            ),
            Hero(
                id=69, name="Bristleback", localized_name="Bristleback",
                internal_name="npc_dota_hero_bristleback",
                primary_attr="str", attack_type="Melee",
                roles=["Carry", "Durable"],
            ),
            Hero(
                id=12, name="Phantom Assassin", localized_name="Phantom Assassin",
                internal_name="npc_dota_hero_phantom_assassin",
                primary_attr="agi", attack_type="Melee",
                roles=["Carry", "Escape"],
            ),
            Hero(
                id=32, name="Riki", localized_name="Riki",
                internal_name="npc_dota_hero_riki",
                primary_attr="agi", attack_type="Melee",
                roles=["Carry", "Escape"],
            ),
            Hero(
                id=57, name="Lifestealer", localized_name="Lifestealer",
                internal_name="npc_dota_hero_life_stealer",
                primary_attr="str", attack_type="Melee",
                roles=["Carry", "Durable"],
            ),
            Hero(
                id=33, name="Enigma", localized_name="Enigma",
                internal_name="npc_dota_hero_enigma",
                primary_attr="int", attack_type="Ranged",
                roles=["Initiator", "Jungler"],
            ),
            Hero(
                id=97, name="Magnus", localized_name="Magnus",
                internal_name="npc_dota_hero_magnataur",
                primary_attr="str", attack_type="Melee",
                roles=["Initiator", "Disabler"],
            ),
            Hero(
                id=26, name="Lion", localized_name="Lion",
                internal_name="npc_dota_hero_lion",
                primary_attr="int", attack_type="Ranged",
                roles=["Support", "Disabler"],
            ),
            Hero(
                id=40, name="Venomancer", localized_name="Venomancer",
                internal_name="npc_dota_hero_venomancer",
                primary_attr="agi", attack_type="Ranged",
                roles=["Support", "Nuker"],
            ),
            Hero(
                id=84, name="Ogre Magi", localized_name="Ogre Magi",
                internal_name="npc_dota_hero_ogre_magi",
                primary_attr="str", attack_type="Melee",
                roles=["Support", "Nuker"],
            ),
            Hero(
                id=110, name="Skywrath Mage", localized_name="Skywrath Mage",
                internal_name="npc_dota_hero_skywrath_mage",
                primary_attr="int", attack_type="Ranged",
                roles=["Support", "Nuker"],
            ),
            Hero(
                id=47, name="Faceless Void", localized_name="Faceless Void",
                internal_name="npc_dota_hero_faceless_void",
                primary_attr="agi", attack_type="Melee",
                roles=["Carry", "Initiator"],
            ),
            Hero(
                id=93, name="Slark", localized_name="Slark",
                internal_name="npc_dota_hero_slark",
                primary_attr="agi", attack_type="Melee",
                roles=["Carry", "Escape"],
            ),
            Hero(
                id=72, name="Alchemist", localized_name="Alchemist",
                internal_name="npc_dota_hero_alchemist",
                primary_attr="str", attack_type="Melee",
                roles=["Carry", "Durable"],
            ),
            Hero(
                id=67, name="Clinkz", localized_name="Clinkz",
                internal_name="npc_dota_hero_clinkz",
                primary_attr="agi", attack_type="Ranged",
                roles=["Carry", "Escape"],
            ),
            Hero(
                id=94, name="Weaver", localized_name="Weaver",
                internal_name="npc_dota_hero_weaver",
                primary_attr="agi", attack_type="Ranged",
                roles=["Carry", "Escape"],
            ),
            Hero(
                id=11, name="Sven", localized_name="Sven",
                internal_name="npc_dota_hero_sven",
                primary_attr="str", attack_type="Melee",
                roles=["Carry", "Disabler"],
            ),
            Hero(
                id=44, name="Phantom Lancer", localized_name="Phantom Lancer",
                internal_name="npc_dota_hero_phantom_lancer",
                primary_attr="agi", attack_type="Melee",
                roles=["Carry", "Escape"],
            ),
            Hero(
                id=18, name="Juggernaut", localized_name="Juggernaut",
                internal_name="npc_dota_hero_juggernaut",
                primary_attr="agi", attack_type="Melee",
                roles=["Carry"],
            ),
            Hero(
                id=91, name="Wraith King", localized_name="Wraith King",
                internal_name="npc_dota_hero_skeleton_king",
                primary_attr="str", attack_type="Melee",
                roles=["Carry", "Durable"],
            ),
            Hero(
                id=120, name="Huskar", localized_name="Huskar",
                internal_name="npc_dota_hero_huskar",
                primary_attr="str", attack_type="Ranged",
                roles=["Carry", "Durable"],
            ),
            Hero(
                id=103, name="Necrophos", localized_name="Necrophos",
                internal_name="npc_dota_hero_necrolyte",
                primary_attr="int", attack_type="Ranged",
                roles=["Nuker", "Durable"],
            ),
            # Phase 20: Counter-Item Intelligence heroes
            Hero(
                id=30, name="Witch Doctor", localized_name="Witch Doctor",
                internal_name="npc_dota_hero_witch_doctor",
                primary_attr="int", attack_type="Ranged",
                roles=["Support", "Nuker"],
            ),
            Hero(
                id=13, name="Puck", localized_name="Puck",
                internal_name="npc_dota_hero_puck",
                primary_attr="int", attack_type="Ranged",
                roles=["Initiator", "Escape"],
            ),
            Hero(
                id=39, name="Queen of Pain", localized_name="Queen of Pain",
                internal_name="npc_dota_hero_queenofpain",
                primary_attr="int", attack_type="Ranged",
                roles=["Nuker", "Escape"],
            ),
            Hero(
                id=17, name="Storm Spirit", localized_name="Storm Spirit",
                internal_name="npc_dota_hero_storm_spirit",
                primary_attr="int", attack_type="Ranged",
                roles=["Carry", "Escape"],
            ),
            Hero(
                id=46, name="Ember Spirit", localized_name="Ember Spirit",
                internal_name="npc_dota_hero_ember_spirit",
                primary_attr="agi", attack_type="Melee",
                roles=["Carry", "Escape"],
            ),
            Hero(
                id=98, name="Timbersaw", localized_name="Timbersaw",
                internal_name="npc_dota_hero_shredder",
                primary_attr="str", attack_type="Melee",
                roles=["Nuker", "Durable"],
            ),
            Hero(
                id=49, name="Dragon Knight", localized_name="Dragon Knight",
                internal_name="npc_dota_hero_dragon_knight",
                primary_attr="str", attack_type="Melee",
                roles=["Carry", "Durable"],
            ),
            Hero(
                id=55, name="Dark Seer", localized_name="Dark Seer",
                internal_name="npc_dota_hero_dark_seer",
                primary_attr="int", attack_type="Melee",
                roles=["Initiator"],
            ),
            Hero(
                id=29, name="Tidehunter", localized_name="Tidehunter",
                internal_name="npc_dota_hero_tidehunter",
                primary_attr="str", attack_type="Melee",
                roles=["Initiator", "Durable"],
            ),
            Hero(
                id=86, name="Rubick", localized_name="Rubick",
                internal_name="npc_dota_hero_rubick",
                primary_attr="int", attack_type="Ranged",
                roles=["Support", "Disabler"],
            ),
            Hero(
                id=43, name="Death Prophet", localized_name="Death Prophet",
                internal_name="npc_dota_hero_death_prophet",
                primary_attr="int", attack_type="Ranged",
                roles=["Nuker", "Pusher"],
            ),
            Hero(
                id=52, name="Leshrac", localized_name="Leshrac",
                internal_name="npc_dota_hero_leshrac",
                primary_attr="int", attack_type="Ranged",
                roles=["Nuker", "Pusher"],
            ),
            Hero(
                id=31, name="Lich", localized_name="Lich",
                internal_name="npc_dota_hero_lich",
                primary_attr="int", attack_type="Ranged",
                roles=["Support", "Nuker"],
            ),
            Hero(
                id=25, name="Lina", localized_name="Lina",
                internal_name="npc_dota_hero_lina",
                primary_attr="int", attack_type="Ranged",
                roles=["Nuker", "Support"],
            ),
            Hero(
                id=35, name="Bounty Hunter", localized_name="Bounty Hunter",
                internal_name="npc_dota_hero_bounty_hunter",
                primary_attr="agi", attack_type="Melee",
                roles=["Escape", "Nuker"],
            ),
            Hero(
                id=88, name="Nyx Assassin", localized_name="Nyx Assassin",
                internal_name="npc_dota_hero_nyx_assassin",
                primary_attr="agi", attack_type="Melee",
                roles=["Initiator", "Escape"],
            ),
            Hero(
                id=60, name="Night Stalker", localized_name="Night Stalker",
                internal_name="npc_dota_hero_night_stalker",
                primary_attr="str", attack_type="Melee",
                roles=["Carry", "Initiator"],
            ),
            Hero(
                id=100, name="Troll Warlord", localized_name="Troll Warlord",
                internal_name="npc_dota_hero_troll_warlord",
                primary_attr="agi", attack_type="Ranged",
                roles=["Carry"],
            ),
            Hero(
                id=62, name="Monkey King", localized_name="Monkey King",
                internal_name="npc_dota_hero_monkey_king",
                primary_attr="agi", attack_type="Melee",
                roles=["Carry"],
            ),
            Hero(
                id=76, name="Mirana", localized_name="Mirana",
                internal_name="npc_dota_hero_mirana",
                primary_attr="agi", attack_type="Ranged",
                roles=["Carry", "Escape"],
            ),
            Hero(
                id=45, name="Silencer", localized_name="Silencer",
                internal_name="npc_dota_hero_silencer",
                primary_attr="int", attack_type="Ranged",
                roles=["Support", "Carry"],
            ),
            Hero(
                id=37, name="Warlock", localized_name="Warlock",
                internal_name="npc_dota_hero_warlock",
                primary_attr="int", attack_type="Ranged",
                roles=["Support"],
            ),
            Hero(
                id=58, name="Enchantress", localized_name="Enchantress",
                internal_name="npc_dota_hero_enchantress",
                primary_attr="int", attack_type="Ranged",
                roles=["Support", "Jungler"],
            ),
            Hero(
                id=112, name="Dark Willow", localized_name="Dark Willow",
                internal_name="npc_dota_hero_dark_willow",
                primary_attr="int", attack_type="Ranged",
                roles=["Support", "Nuker"],
            ),
            Hero(
                id=74, name="Invoker", localized_name="Invoker",
                internal_name="npc_dota_hero_invoker",
                primary_attr="int", attack_type="Ranged",
                roles=["Carry", "Nuker"],
            ),
            Hero(
                id=36, name="Razor", localized_name="Razor",
                internal_name="npc_dota_hero_razor",
                primary_attr="agi", attack_type="Ranged",
                roles=["Carry"],
            ),
            Hero(
                id=51, name="Brewmaster", localized_name="Brewmaster",
                internal_name="npc_dota_hero_brewmaster",
                primary_attr="str", attack_type="Melee",
                roles=["Carry", "Initiator"],
            ),
            Hero(
                id=53, name="Naga Siren", localized_name="Naga Siren",
                internal_name="npc_dota_hero_naga_siren",
                primary_attr="agi", attack_type="Melee",
                roles=["Carry"],
            ),
            Hero(
                id=63, name="Chaos Knight", localized_name="Chaos Knight",
                internal_name="npc_dota_hero_chaos_knight",
                primary_attr="str", attack_type="Melee",
                roles=["Carry", "Initiator"],
            ),
            Hero(
                id=71, name="Chen", localized_name="Chen",
                internal_name="npc_dota_hero_chen",
                primary_attr="int", attack_type="Ranged",
                roles=["Support", "Jungler"],
            ),
            Hero(
                id=101, name="Meepo", localized_name="Meepo",
                internal_name="npc_dota_hero_meepo",
                primary_attr="agi", attack_type="Melee",
                roles=["Carry"],
            ),
            Hero(
                id=87, name="Disruptor", localized_name="Disruptor",
                internal_name="npc_dota_hero_disruptor",
                primary_attr="int", attack_type="Ranged",
                roles=["Support", "Disabler"],
            ),
            Hero(
                id=104, name="Grimstroke", localized_name="Grimstroke",
                internal_name="npc_dota_hero_grimstroke",
                primary_attr="int", attack_type="Ranged",
                roles=["Support", "Nuker"],
            ),
            Hero(
                id=41, name="Sand King", localized_name="Sand King",
                internal_name="npc_dota_hero_sand_king",
                primary_attr="str", attack_type="Melee",
                roles=["Initiator"],
            ),
            Hero(
                id=96, name="Underlord", localized_name="Underlord",
                internal_name="npc_dota_hero_abyssal_underlord",
                primary_attr="str", attack_type="Melee",
                roles=["Durable", "Nuker"],
            ),
            Hero(
                id=38, name="Treant Protector", localized_name="Treant Protector",
                internal_name="npc_dota_hero_treant",
                primary_attr="str", attack_type="Melee",
                roles=["Support"],
            ),
            Hero(
                id=105, name="Arc Warden", localized_name="Arc Warden",
                internal_name="npc_dota_hero_arc_warden",
                primary_attr="agi", attack_type="Ranged",
                roles=["Carry"],
            ),
        ]
        session.add_all(extra_heroes)

        # Seed test items (extended for rules engine coverage)
        items = [
            Item(id=1, name="Blink Dagger", internal_name="blink", cost=2250),
            Item(id=2, name="Black King Bar", internal_name="black_king_bar", cost=4050),
            Item(id=29, name="Quelling Blade", internal_name="quelling_blade", cost=100),
            Item(id=36, name="Magic Stick", internal_name="magic_stick", cost=200),
            Item(id=40, name="Dust of Appearance", internal_name="dust", cost=80),
            Item(id=43, name="Sentry Ward", internal_name="ward_sentry", cost=50),
            Item(id=48, name="Power Treads", internal_name="power_treads", cost=1400),
            Item(id=50, name="Phase Boots", internal_name="phase_boots", cost=1500),
            Item(id=99, name="Soul Ring", internal_name="soul_ring", cost=805),
            Item(id=102, name="Force Staff", internal_name="force_staff", cost=2200),
            Item(id=116, name="Black King Bar", internal_name="bkb", cost=4050),
            Item(id=119, name="Shiva's Guard", internal_name="shivas_guard", cost=4750),
            Item(id=180, name="Arcane Boots", internal_name="arcane_boots", cost=1300),
            Item(id=225, name="Monkey King Bar", internal_name="monkey_king_bar", cost=4975),
            Item(id=235, name="Assault Cuirass", internal_name="assault", cost=5250),
            Item(id=249, name="Silver Edge", internal_name="silver_edge", cost=5450),
            Item(id=271, name="Spirit Vessel", internal_name="spirit_vessel", cost=2980),
            # Recipe and neutral items for filter testing
            Item(id=300, name="Recipe: Assault Cuirass", internal_name="recipe_assault",
                 cost=1300, is_recipe=True),
            Item(id=301, name="Mysterious Hat", internal_name="mysterious_hat",
                 cost=0, is_neutral=True, tier=1,
                 active_desc="Grants +1 mana regeneration"),
            Item(id=350, name="Chipped Vest", internal_name="chipped_vest",
                 cost=0, is_neutral=True, tier=1,
                 active_desc="Returns 28 damage when attacked"),
            Item(id=351, name="Psychic Headband", internal_name="psychic_headband",
                 cost=0, is_neutral=True, tier=3,
                 active_desc="Pushes the target 400 units away"),
            Item(id=352, name="Spider Legs", internal_name="spider_legs",
                 cost=0, is_neutral=True, tier=5,
                 active_desc="Grants free pathing and 25% move speed"),
            # Items for new rules (Phase 14)
            Item(id=56, name="Infused Raindrops", internal_name="infused_raindrop", cost=225),
            Item(id=187, name="Mekansm", internal_name="mekansm", cost=1775),
            Item(id=231, name="Pipe of Insight", internal_name="pipe", cost=3475),
            Item(id=190, name="Orchid Malevolence", internal_name="orchid", cost=3475),
            Item(id=168, name="Heaven's Halberd", internal_name="heavens_halberd", cost=3550),
            Item(id=185, name="Ghost Scepter", internal_name="ghost", cost=1500),
            # Expensive item to test budget filtering
            Item(id=302, name="Divine Rapier", internal_name="rapier", cost=5950),
            # Phase 20: Counter-Item Intelligence items
            Item(id=100, name="Eul's Scepter of Divinity", internal_name="cyclone", cost=2725),
            Item(id=226, name="Lotus Orb", internal_name="lotus_orb", cost=3850),
            Item(id=194, name="Linken's Sphere", internal_name="sphere", cost=4600),
            Item(id=250, name="Scythe of Vyse", internal_name="sheepstick", cost=5675),
            Item(id=206, name="Rod of Atos", internal_name="rod_of_atos", cost=2750),
        ]
        session.add_all(items)

        # Seed test ability data for Anti-Mage (hero_id=1) and Crystal Maiden (hero_id=3)
        ability_data = [
            HeroAbilityData(
                hero_id=1,
                abilities_json={
                    "antimage_mana_break": {
                        "dname": "Mana Break",
                        "behavior": "Passive",
                        "dmg_type": "Physical",
                        "bkbpierce": "No",
                        "dispellable": None,
                    },
                    "antimage_blink": {
                        "dname": "Blink",
                        "behavior": ["Unit Target", "Point Target"],
                        "dmg_type": None,
                        "bkbpierce": None,
                        "dispellable": None,
                    },
                    "antimage_counterspell": {
                        "dname": "Counterspell",
                        "behavior": "Passive",
                        "dmg_type": None,
                        "bkbpierce": None,
                        "dispellable": None,
                    },
                    "antimage_mana_void": {
                        "dname": "Mana Void",
                        "behavior": ["Unit Target", "AOE"],
                        "dmg_type": "Magical",
                        "bkbpierce": "No",
                        "dispellable": None,
                    },
                },
            ),
            HeroAbilityData(
                hero_id=3,
                abilities_json={
                    "crystal_maiden_crystal_nova": {
                        "dname": "Crystal Nova",
                        "behavior": ["AOE", "Point Target"],
                        "dmg_type": "Magical",
                        "bkbpierce": "No",
                        "dispellable": "Yes",
                    },
                    "crystal_maiden_frostbite": {
                        "dname": "Frostbite",
                        "behavior": "Unit Target",
                        "dmg_type": "Magical",
                        "bkbpierce": "No",
                        "dispellable": "Yes",
                    },
                    "crystal_maiden_freezing_field": {
                        "dname": "Freezing Field",
                        "behavior": ["No Target", "Channeled"],
                        "dmg_type": "Magical",
                        "bkbpierce": "No",
                        "dispellable": None,
                    },
                },
            ),
            # Phase 20: Counter-Item Intelligence ability data
            HeroAbilityData(
                hero_id=30,  # Witch Doctor
                abilities_json={
                    "witch_doctor_paralyzing_cask": {
                        "dname": "Paralyzing Cask",
                        "behavior": "Unit Target",
                        "dmg_type": "Magical",
                        "bkbpierce": "No",
                        "dispellable": "Strong Dispels Only",
                    },
                    "witch_doctor_voodoo_restoration": {
                        "dname": "Voodoo Restoration",
                        "behavior": ["No Target", "Toggle"],
                        "dmg_type": None,
                        "bkbpierce": None,
                        "dispellable": None,
                    },
                    "witch_doctor_maledict": {
                        "dname": "Maledict",
                        "behavior": ["AOE", "Point Target"],
                        "dmg_type": "Magical",
                        "bkbpierce": "No",
                        "dispellable": "No",
                    },
                    "witch_doctor_death_ward": {
                        "dname": "Death Ward",
                        "behavior": ["Channeled", "Point Target"],
                        "dmg_type": "Physical",
                        "bkbpierce": "Yes",
                        "dispellable": None,
                    },
                },
            ),
            HeroAbilityData(
                hero_id=33,  # Enigma
                abilities_json={
                    "enigma_eidolons": {
                        "dname": "Eidolons",
                        "behavior": "No Target",
                        "dmg_type": None,
                        "bkbpierce": None,
                        "dispellable": None,
                    },
                    "enigma_demonic_conversion": {
                        "dname": "Demonic Conversion",
                        "behavior": "Unit Target",
                        "dmg_type": None,
                        "bkbpierce": "No",
                        "dispellable": None,
                    },
                    "enigma_midnight_pulse": {
                        "dname": "Midnight Pulse",
                        "behavior": ["AOE", "Point Target"],
                        "dmg_type": "Pure",
                        "bkbpierce": "No",
                        "dispellable": None,
                    },
                    "enigma_black_hole": {
                        "dname": "Black Hole",
                        "behavior": ["AOE", "Channeled"],
                        "dmg_type": "Pure",
                        "bkbpierce": "Yes",
                        "dispellable": None,
                    },
                },
            ),
            HeroAbilityData(
                hero_id=13,  # Puck
                abilities_json={
                    "puck_illusory_orb": {
                        "dname": "Illusory Orb",
                        "behavior": "Point Target",
                        "dmg_type": "Magical",
                        "bkbpierce": "No",
                        "dispellable": None,
                    },
                    "puck_waning_rift": {
                        "dname": "Waning Rift",
                        "behavior": "No Target",
                        "dmg_type": "Magical",
                        "bkbpierce": "No",
                        "dispellable": "Yes",
                    },
                    "puck_phase_shift": {
                        "dname": "Phase Shift",
                        "behavior": "No Target",
                        "dmg_type": None,
                        "bkbpierce": None,
                        "dispellable": None,
                    },
                    "puck_dream_coil": {
                        "dname": "Dream Coil",
                        "behavior": ["AOE", "Point Target"],
                        "dmg_type": "Magical",
                        "bkbpierce": "No",
                        "dispellable": "Yes",
                    },
                },
            ),
            HeroAbilityData(
                hero_id=39,  # Queen of Pain
                abilities_json={
                    "queenofpain_shadow_strike": {
                        "dname": "Shadow Strike",
                        "behavior": "Unit Target",
                        "dmg_type": "Magical",
                        "bkbpierce": "No",
                        "dispellable": "Yes",
                    },
                    "queenofpain_blink": {
                        "dname": "Blink",
                        "behavior": "Point Target",
                        "dmg_type": None,
                        "bkbpierce": None,
                        "dispellable": None,
                    },
                    "queenofpain_scream_of_pain": {
                        "dname": "Scream of Pain",
                        "behavior": "No Target",
                        "dmg_type": "Magical",
                        "bkbpierce": "No",
                        "dispellable": None,
                    },
                    "queenofpain_sonic_wave": {
                        "dname": "Sonic Wave",
                        "behavior": "Point Target",
                        "dmg_type": "Pure",
                        "bkbpierce": "No",
                        "dispellable": None,
                    },
                },
            ),
            HeroAbilityData(
                hero_id=17,  # Storm Spirit
                abilities_json={
                    "storm_spirit_static_remnant": {
                        "dname": "Static Remnant",
                        "behavior": "No Target",
                        "dmg_type": "Magical",
                        "bkbpierce": "No",
                        "dispellable": None,
                    },
                    "storm_spirit_electric_vortex": {
                        "dname": "Electric Vortex",
                        "behavior": "Unit Target",
                        "dmg_type": None,
                        "bkbpierce": "No",
                        "dispellable": "Yes",
                    },
                    "storm_spirit_overload": {
                        "dname": "Overload",
                        "behavior": "Passive",
                        "dmg_type": "Magical",
                        "bkbpierce": "No",
                        "dispellable": None,
                    },
                    "storm_spirit_ball_lightning": {
                        "dname": "Ball Lightning",
                        "behavior": ["No Target", "Point Target"],
                        "dmg_type": None,
                        "bkbpierce": "No",
                        "dispellable": None,
                    },
                },
            ),
            HeroAbilityData(
                hero_id=69,  # Bristleback
                abilities_json={
                    "bristleback_viscous_nasal_goo": {
                        "dname": "Viscous Nasal Goo",
                        "behavior": "Unit Target",
                        "dmg_type": None,
                        "bkbpierce": "No",
                        "dispellable": "Yes",
                    },
                    "bristleback_quill_spray": {
                        "dname": "Quill Spray",
                        "behavior": "No Target",
                        "dmg_type": "Physical",
                        "bkbpierce": "No",
                        "dispellable": None,
                    },
                    "bristleback_bristleback": {
                        "dname": "Bristleback",
                        "behavior": "Passive",
                        "dmg_type": None,
                        "bkbpierce": None,
                        "dispellable": None,
                    },
                    "bristleback_warpath": {
                        "dname": "Warpath",
                        "behavior": "Passive",
                        "dmg_type": None,
                        "bkbpierce": None,
                        "dispellable": None,
                    },
                },
            ),
            HeroAbilityData(
                hero_id=12,  # Phantom Assassin
                abilities_json={
                    "phantom_assassin_stifling_dagger": {
                        "dname": "Stifling Dagger",
                        "behavior": "Unit Target",
                        "dmg_type": "Physical",
                        "bkbpierce": "No",
                        "dispellable": None,
                    },
                    "phantom_assassin_phantom_strike": {
                        "dname": "Phantom Strike",
                        "behavior": "Unit Target",
                        "dmg_type": None,
                        "bkbpierce": None,
                        "dispellable": None,
                    },
                    "phantom_assassin_blur": {
                        "dname": "Blur",
                        "behavior": "Passive",
                        "dmg_type": None,
                        "bkbpierce": None,
                        "dispellable": None,
                    },
                    "phantom_assassin_coup_de_grace": {
                        "dname": "Coup de Grace",
                        "behavior": "Passive",
                        "dmg_type": None,
                        "bkbpierce": None,
                        "dispellable": None,
                    },
                },
            ),
            HeroAbilityData(
                hero_id=57,  # Lifestealer
                abilities_json={
                    "life_stealer_feast": {
                        "dname": "Feast",
                        "behavior": "Passive",
                        "dmg_type": None,
                        "bkbpierce": None,
                        "dispellable": None,
                    },
                    "life_stealer_rage": {
                        "dname": "Rage",
                        "behavior": "No Target",
                        "dmg_type": None,
                        "bkbpierce": "No",
                        "dispellable": "Yes",
                    },
                    "life_stealer_open_wounds": {
                        "dname": "Open Wounds",
                        "behavior": "Unit Target",
                        "dmg_type": None,
                        "bkbpierce": "No",
                        "dispellable": "Yes",
                    },
                    "life_stealer_infest": {
                        "dname": "Infest",
                        "behavior": "Unit Target",
                        "dmg_type": "Magical",
                        "bkbpierce": "Yes",
                        "dispellable": None,
                    },
                },
            ),
            HeroAbilityData(
                hero_id=93,  # Slark
                abilities_json={
                    "slark_dark_pact": {
                        "dname": "Dark Pact",
                        "behavior": "No Target",
                        "dmg_type": "Magical",
                        "bkbpierce": "No",
                        "dispellable": None,
                    },
                    "slark_pounce": {
                        "dname": "Pounce",
                        "behavior": ["No Target", "Point Target"],
                        "dmg_type": None,
                        "bkbpierce": "No",
                        "dispellable": "Yes",
                    },
                    "slark_essence_shift": {
                        "dname": "Essence Shift",
                        "behavior": "Passive",
                        "dmg_type": None,
                        "bkbpierce": None,
                        "dispellable": None,
                    },
                    "slark_shadow_dance": {
                        "dname": "Shadow Dance",
                        "behavior": "No Target",
                        "dmg_type": None,
                        "bkbpierce": None,
                        "dispellable": None,
                    },
                },
            ),
            HeroAbilityData(
                hero_id=32,  # Riki
                abilities_json={
                    "riki_smoke_screen": {
                        "dname": "Smoke Screen",
                        "behavior": ["AOE", "Point Target"],
                        "dmg_type": None,
                        "bkbpierce": "No",
                        "dispellable": None,
                    },
                    "riki_blink_strike": {
                        "dname": "Blink Strike",
                        "behavior": "Unit Target",
                        "dmg_type": "Magical",
                        "bkbpierce": "No",
                        "dispellable": None,
                    },
                    "riki_cloak_and_dagger": {
                        "dname": "Cloak and Dagger",
                        "behavior": "Passive",
                        "dmg_type": None,
                        "bkbpierce": None,
                        "dispellable": None,
                    },
                    "riki_tricks_of_the_trade": {
                        "dname": "Tricks of the Trade",
                        "behavior": ["AOE", "Point Target", "Channeled"],
                        "dmg_type": "Physical",
                        "bkbpierce": "No",
                        "dispellable": None,
                    },
                },
            ),
        ]
        session.add_all(ability_data)

        # Seed test timing data for Anti-Mage (hero_id=1)
        timing_data = [
            ItemTimingData(
                hero_id=1,
                timings_json={
                    "bfury": [
                        {"time": 720, "games": "40", "wins": "30"},
                        {"time": 900, "games": "277", "wins": "175"},
                        {"time": 1200, "games": "284", "wins": "114"},
                        {"time": 1500, "games": "19", "wins": "8"},
                    ],
                    "manta": [
                        {"time": 1200, "games": "150", "wins": "95"},
                        {"time": 1500, "games": "300", "wins": "170"},
                        {"time": 1800, "games": "80", "wins": "30"},
                    ],
                },
            ),
        ]
        session.add_all(timing_data)

        await session.commit()

    # Load data_cache from seeded DB so cache-based tests work
    from data.cache import data_cache
    async with test_async_session() as session:
        await data_cache.load(session)

    yield

    # Drop all tables for isolation
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def test_client(test_db_setup):
    """Create an async test client with database dependency override."""
    from middleware.rate_limiter import rate_limiter
    # Clear rate limiter state between tests to prevent 429 interference
    rate_limiter._last_request.clear()

    async def override_get_db():
        async with test_async_session() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_db_session(test_db_setup):
    """Yield a raw async session for unit tests that need DB access but not HTTP."""
    async with test_async_session() as session:
        yield session
