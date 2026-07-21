from __future__ import annotations

import base64
import html
import random
import time
import uuid
from pathlib import Path

import streamlit as st

from scenario_data import BOSS_CHALLENGES, FLOORS
from sheets_client import append_result


APP_DIR = Path(__file__).parent
ASSET_DIR = APP_DIR / "assets"
TOTAL_SCENES = sum(len(floor["scenes"]) for floor in FLOORS)
DEPARTMENTS = ["전략기획", "전략투자", "브랜드성장", "기타"]
BONUS_SUCCESS_RATES = (50, 30, 20, 10, 5)


st.set_page_config(
    page_title="담합의 탑",
    page_icon="T",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def apply_style() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #101319;
            --panel: #1b2230;
            --panel-2: #252f40;
            --paper: #f5f2e9;
            --yellow: #ffd44d;
            --red: #e55454;
            --green: #54c58d;
            --blue: #76b9e8;
        }
        .stApp { background: var(--ink); }
        .block-container { max-width: 1080px; padding-top: 1.5rem; padding-bottom: 3rem; }
        #MainMenu, header, footer { visibility: hidden; }
        h1, h2, h3, p, label, .stMarkdown, .stCaption, .stTextInput, .stSelectbox {
            font-family: "Courier New", "Malgun Gothic", monospace !important;
        }
        h1 { color: var(--yellow); border-bottom: 4px solid var(--yellow); padding-bottom: 0.45rem; }
        h2, h3 { color: var(--paper); }
        .pixel-panel {
            border: 3px solid var(--paper);
            box-shadow: 6px 6px 0 #000;
            background: var(--panel);
            padding: 1rem 1.1rem;
            margin: 0.55rem 0 1rem;
        }
        .tower-frame {
            min-height: 245px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: repeating-linear-gradient(0deg, #20293a 0 2px, #18202e 2px 4px);
            border: 4px solid var(--yellow);
            box-shadow: 8px 8px 0 #000;
            color: var(--yellow);
            font-size: 1.4rem;
            font-weight: 700;
            text-align: center;
        }
        .sprite-placeholder {
            min-height: 150px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 3px solid currentColor;
            background: #0b0e14;
            color: var(--yellow);
            font-size: 1rem;
            font-weight: 700;
            text-align: center;
            padding: 1rem;
        }
        .enemy-sprite { color: var(--red); }
        .hero-sprite { color: var(--green); }
        .battle-arena {
            position: relative;
            width: 100%;
            aspect-ratio: 16 / 9;
            overflow: hidden;
            margin: 0.7rem 0 1.15rem;
            border: 4px solid var(--paper);
            box-shadow: 7px 7px 0 #000;
            background-position: center;
            background-repeat: no-repeat;
            background-size: cover;
            image-rendering: pixelated;
        }
        .battle-arena::after {
            content: "";
            position: absolute;
            inset: 0;
            pointer-events: none;
            box-shadow: inset 0 0 28px rgba(0, 0, 0, 0.58);
        }
        .battle-sprite {
            position: absolute;
            z-index: 2;
            display: block;
            object-fit: contain;
            image-rendering: pixelated;
            filter: drop-shadow(7px 9px 0 rgba(0, 0, 0, 0.45));
        }
        .battle-enemy {
            right: 16.25%;
            bottom: 44%;
            width: 30%;
            max-height: 72%;
        }
        .battle-hero {
            left: 10%;
            bottom: 9.5%;
            width: 41%;
        }
        .battle-status {
            position: absolute;
            z-index: 3;
            width: min(38%, 330px);
            padding: 0.55rem 0.65rem 0.62rem;
            border: 3px solid var(--paper);
            background: rgba(11, 14, 20, 0.9);
            box-shadow: 4px 4px 0 #000;
        }
        .battle-status-enemy { top: 4%; left: 3%; }
        .battle-status-player { right: 3%; bottom: 4%; }
        .battle-status .battle-name { font-size: clamp(0.72rem, 1.7vw, 1.05rem); }
        .battle-status .battle-role { font-size: clamp(0.58rem, 1.25vw, 0.8rem); }
        .battle-status .hp-track { height: 11px; }
        .hud {
            display: flex;
            flex-wrap: wrap;
            gap: 0.65rem;
            align-items: center;
            color: var(--paper);
            margin-bottom: 0.25rem;
        }
        .hud-chip {
            padding: 0.28rem 0.52rem;
            background: #000;
            border: 2px solid var(--paper);
            color: var(--paper);
            font-size: 0.82rem;
        }
        .battle-name { color: var(--paper); font-size: 1.1rem; font-weight: 700; }
        .battle-role { color: var(--blue); font-size: 0.84rem; }
        .hp-track { height: 12px; background: #05070a; border: 2px solid var(--paper); margin-top: 0.35rem; }
        .hp-fill { height: 100%; background: var(--green); width: 82%; }
        .enemy-hp .hp-fill { background: var(--red); width: 76%; }
        .dialogue { color: var(--paper); line-height: 1.75; font-size: 1.04rem; }
        .danger-note { color: var(--yellow); font-size: 0.84rem; margin: 0.35rem 0 0.7rem; }
        .followup-step {
            color: var(--cyan);
            font-size: 0.78rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }
        .encounter-label {
            color: var(--red);
            font-size: 0.76rem;
            font-weight: 800;
            margin-bottom: 0.35rem;
        }
        div.stButton > button {
            border-radius: 0 !important;
            border: 3px solid var(--paper) !important;
            box-shadow: 4px 4px 0 #000 !important;
            background: var(--panel-2) !important;
            color: var(--paper) !important;
            min-height: 3.2rem !important;
            white-space: normal !important;
            text-align: left !important;
            font-family: "Courier New", "Malgun Gothic", monospace !important;
        }
        div.stButton > button:hover:enabled { border-color: var(--yellow) !important; color: var(--yellow) !important; }
        div.stButton > button:disabled { opacity: 0.42; }
        div[data-testid="stMetric"] { border: 2px solid var(--paper); background: var(--panel); padding: 0.55rem; }
        div[data-testid="stMetricValue"] {
            color: var(--yellow);
            line-height: 1.2 !important;
            min-height: 1.2em;
        }
        div[data-testid="stMetricValue"] p { line-height: 1.2 !important; }
        .feedback-good { color: var(--green); font-weight: 700; }
        .feedback-risk { color: var(--red); font-weight: 700; }
        .small-muted { color: #c5cbd4; font-size: 0.88rem; }
        div.st-key-floor_feedback_parchment {
            position: relative;
            isolation: isolate;
            margin: 1rem 0 1.6rem;
            padding: 2.3rem 2.5rem 1.7rem;
            border: 4px solid #5d381c;
            border-radius: 2px;
            background-color: #d8bd79;
            background-image:
                radial-gradient(circle at 15% 18%, rgba(255, 244, 188, 0.5) 0 8%, transparent 22%),
                radial-gradient(circle at 82% 72%, rgba(111, 67, 27, 0.16) 0 7%, transparent 24%),
                repeating-linear-gradient(0deg, rgba(92, 55, 24, 0.04) 0 1px, transparent 1px 5px);
            box-shadow: inset 0 0 40px rgba(80, 45, 18, 0.34), 8px 8px 0 #000;
            color: #352313;
        }
        div.st-key-floor_feedback_parchment::before,
        div.st-key-floor_feedback_parchment::after {
            content: "";
            position: absolute;
            z-index: -1;
            left: 1.3%;
            right: 1.3%;
            height: 15px;
            border: 2px solid #4b2b16;
            background: #966632;
            box-shadow: inset 0 3px 0 rgba(255, 229, 155, 0.28), 3px 3px 0 rgba(0, 0, 0, 0.4);
        }
        div.st-key-floor_feedback_parchment::before { top: -11px; }
        div.st-key-floor_feedback_parchment::after { bottom: -11px; }
        .parchment-title,
        .parchment-closing,
        .parchment-result-title,
        .parchment-feedback,
        .parchment-best,
        .parchment-lessons,
        .parchment-terms,
        .parchment-memory,
        .parchment-review {
            font-family: "Batang", "Nanum Myeongjo", "Noto Serif KR", serif !important;
            color: #352313 !important;
        }
        .parchment-title {
            margin: 0;
            padding-bottom: 0;
            border-bottom: 0;
            font-size: 2rem;
            font-weight: 800;
            text-align: center;
        }
        .parchment-rule {
            width: 72%;
            height: 3px;
            margin: 0.7rem auto 1rem;
            background: #65401f;
            box-shadow: 0 3px 0 rgba(255, 238, 177, 0.35);
        }
        .parchment-closing {
            margin: 0 0 1.1rem;
            font-size: 1rem;
            line-height: 1.75;
            text-align: center;
        }
        .parchment-lessons {
            margin: 1rem 0 0.7rem;
            padding: 0.85rem 0.95rem;
            border-top: 2px solid rgba(75, 43, 22, 0.58);
            border-bottom: 2px solid rgba(75, 43, 22, 0.58);
            line-height: 1.65;
        }
        .parchment-lessons strong { color: #3a2514 !important; }
        .parchment-lessons ul { margin: 0.45rem 0 0; padding-left: 1.25rem; }
        .parchment-lessons li { margin: 0.2rem 0; }
        .parchment-terms {
            margin: 0.7rem 0 0.95rem;
            padding: 0.65rem 0;
            border-bottom: 1px solid rgba(75, 43, 22, 0.42);
            font-size: 0.88rem;
            line-height: 1.6;
        }
        .parchment-terms ul { margin: 0.35rem 0 0; padding-left: 1.25rem; }
        .parchment-terms li { margin: 0.15rem 0; }
        .parchment-result {
            padding: 1rem 0.25rem 0.9rem;
            border-top: 1px solid rgba(75, 43, 22, 0.48);
        }
        .parchment-result-title { font-size: 1rem; font-weight: 800; }
        .parchment-result-title.good { color: #315b35 !important; }
        .parchment-result-title.risk { color: #8b2722 !important; }
        .parchment-feedback { margin: 0.55rem 0; line-height: 1.68; }
        .parchment-best { margin: 0; color: #624524 !important; font-size: 0.88rem; line-height: 1.6; }
        .parchment-score { margin: 0.2rem 0 0.55rem; color: #785420 !important; font-size: 0.82rem; font-weight: 700; }
        .parchment-memory {
            margin: 0.65rem 0 0.55rem;
            padding: 0.7rem 0.8rem;
            border-left: 5px solid #6f451f;
            background: rgba(255, 243, 191, 0.34);
            font-size: 0.95rem;
            font-weight: 800;
            line-height: 1.6;
        }
        .parchment-review { margin-top: 0.55rem; font-size: 0.9rem; line-height: 1.65; }
        .parchment-review summary {
            cursor: pointer;
            color: #573719 !important;
            font-weight: 800;
        }
        .parchment-review[open] summary { margin-bottom: 0.65rem; }
        .review-label { margin: 0.55rem 0 0.12rem; color: #6a431f !important; font-weight: 800; }
        .review-choice { margin: 0 0 0.35rem; color: #24170e !important; line-height: 1.65; }
        div.st-key-floor_feedback_parchment div[data-testid="stMetric"] {
            border: 1px solid rgba(75, 43, 22, 0.52);
            background: rgba(255, 246, 202, 0.24);
            box-shadow: none;
        }
        div.st-key-floor_feedback_parchment div[data-testid="stMetricLabel"],
        div.st-key-floor_feedback_parchment div[data-testid="stMetricLabel"] * {
            color: #090705 !important;
            opacity: 1 !important;
            font-family: "Batang", "Nanum Myeongjo", "Noto Serif KR", serif !important;
        }
        div.st-key-floor_feedback_parchment div[data-testid="stMetricValue"],
        div.st-key-floor_feedback_parchment div[data-testid="stMetricValue"] * {
            color: #050403 !important;
            opacity: 1 !important;
            font-family: "Batang", "Nanum Myeongjo", "Noto Serif KR", serif !important;
            font-weight: 900 !important;
            text-shadow: none !important;
        }
        div.st-key-floor_feedback_parchment div.stButton > button {
            border-color: #3d2413 !important;
            background: #533019 !important;
            color: #f5df9f !important;
            box-shadow: 4px 4px 0 rgba(48, 26, 12, 0.65) !important;
            text-align: center !important;
            font-family: "Batang", "Nanum Myeongjo", "Noto Serif KR", serif !important;
        }
        div.st-key-floor_feedback_parchment div.stButton > button:hover:enabled {
            border-color: #8a5125 !important;
            background: #6c3f1e !important;
            color: #fff0bd !important;
        }
        .ending-scene {
            min-height: 500px;
            display: grid;
            grid-template-columns: minmax(280px, 42%) 1fr;
            align-items: center;
            gap: 1rem;
            overflow: hidden;
            border: 4px solid #c9a84d;
            box-shadow: 8px 8px 0 #000;
            background: repeating-linear-gradient(0deg, #171728 0 5px, #1e1b36 5px 10px);
        }
        .ending-hero {
            width: 100%;
            height: 490px;
            object-fit: contain;
            object-position: center bottom;
            image-rendering: pixelated;
            filter: drop-shadow(0 0 18px rgba(255, 218, 84, 0.32));
        }
        .ending-scene.denied {
            border-color: #72568f;
            background: repeating-linear-gradient(0deg, #15131e 0 5px, #21182d 5px 10px);
        }
        .ending-hero.denied {
            filter: saturate(0.76) brightness(0.84) drop-shadow(0 0 18px rgba(132, 76, 172, 0.42));
        }
        .ending-copy { padding: 2rem 2.2rem 2rem 0.5rem; }
        .ending-kicker { color: #7fd7f2; font-size: 0.82rem; font-weight: 800; }
        .ending-title {
            margin: 0.45rem 0 1rem;
            color: #ffd85b;
            font-family: "Batang", "Nanum Myeongjo", "Noto Serif KR", serif !important;
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.35;
        }
        .ending-title.denied { color: #c9a3dd; }
        .ending-message { color: var(--paper); line-height: 1.75; }
        @media (max-width: 680px) {
            .block-container { padding: 1rem 0.85rem 2rem; }
            .tower-frame { min-height: 180px; }
            .sprite-placeholder { min-height: 105px; }
            .battle-arena { border-width: 3px; box-shadow: 5px 5px 0 #000; }
            .battle-enemy { right: 15.25%; bottom: 43.75%; width: 32%; }
            .battle-hero { left: 10.5%; bottom: 9.75%; width: 40%; }
            .battle-status { padding: 0.3rem 0.38rem 0.36rem; border-width: 2px; }
            .battle-status .hp-track { height: 8px; margin-top: 0.2rem; }
            div.st-key-floor_feedback_parchment { padding: 1.7rem 1rem 1.25rem; }
            .parchment-title { font-size: 1.55rem; }
            .parchment-closing { text-align: left; }
            .parchment-lessons { padding: 0.75rem 0.4rem; }
            .ending-scene { min-height: 0; grid-template-columns: 1fr; }
            .ending-hero { height: 340px; }
            .ending-copy { padding: 0 1.2rem 1.5rem; text-align: center; }
            .ending-title { font-size: 1.55rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    parchment_path = ASSET_DIR / "parchment_scroll.png"
    if parchment_path.exists():
        parchment_data = base64.b64encode(parchment_path.read_bytes()).decode("ascii")
        st.markdown(
            f"""
            <style>
            div.st-key-floor_feedback_parchment {{
                box-sizing: border-box;
                width: 100%;
                max-width: 900px;
                margin: 1rem auto 2rem;
                padding: 0.4rem 1rem 0.2rem;
                border-style: solid;
                border-width: 118px 78px 110px;
                border-image-source: url("data:image/png;base64,{parchment_data}");
                border-image-slice: 180 150 180 150 fill;
                border-image-width: 118px 78px 110px;
                border-image-repeat: stretch;
                border-radius: 0;
                background: none;
                box-shadow: none;
                filter: drop-shadow(8px 9px 0 rgba(0, 0, 0, 0.72));
            }}
            div.st-key-floor_feedback_parchment::before,
            div.st-key-floor_feedback_parchment::after {{ display: none; }}
            @media (max-width: 680px) {{
                div.st-key-floor_feedback_parchment {{
                    padding: 0.2rem 0.55rem 0;
                    border-width: 76px 34px 70px;
                    border-image-width: 76px 34px 70px;
                    filter: drop-shadow(5px 6px 0 rgba(0, 0, 0, 0.68));
                }}
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )


def init_state() -> None:
    defaults = {
        "page": "landing",
        "player": {},
        "floor_index": 0,
        "scene_index": 0,
        "selections": [],
        "main_score": 0,
        "main_started_at": None,
        "main_seconds": None,
        "risk_used": False,
        "risk_success": False,
        "pending_followup": None,
        "main_choice_orders": {},
        "followup_choice_orders": {},
        "show_floor_feedback": False,
        "bonus_score": 0,
        "bonus_streak": 0,
        "bonus_attempts": 0,
        "bonus_result": None,
        "record_code": None,
        "submission_status": None,
        "submission_message": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_game() -> None:
    game_keys = [
        "page",
        "player",
        "floor_index",
        "scene_index",
        "selections",
        "main_score",
        "main_started_at",
        "main_seconds",
        "risk_used",
        "risk_success",
        "pending_followup",
        "main_choice_orders",
        "followup_choice_orders",
        "show_floor_feedback",
        "bonus_score",
        "bonus_streak",
        "bonus_attempts",
        "bonus_result",
        "record_code",
        "submission_status",
        "submission_message",
        "player_name",
        "player_department",
    ]
    for key in game_keys:
        st.session_state.pop(key, None)
    init_state()


def seconds_text(seconds: int | None) -> str:
    if seconds is None:
        return "측정 전"
    minutes, remainder = divmod(seconds, 60)
    return f"{minutes:02d}:{remainder:02d}"


def shuffled_scene_options(floor_number: int, scene_index: int, scene: dict, field: str) -> list[dict]:
    state_key = "main_choice_orders" if field == "choices" else "followup_choice_orders"
    scene_key = f"{floor_number}:{scene_index}"
    options_by_key = {option["key"]: option for option in scene[field]}
    saved_order = st.session_state[state_key].get(scene_key)

    if saved_order is None or set(saved_order) != set(options_by_key):
        saved_order = list(options_by_key)
        random.shuffle(saved_order)
        updated_orders = dict(st.session_state[state_key])
        updated_orders[scene_key] = saved_order
        st.session_state[state_key] = updated_orders

    return [options_by_key[key] for key in saved_order]


def render_sprite(filename: str, label: str, role: str) -> None:
    image_path = ASSET_DIR / filename
    if image_path.exists():
        st.image(str(image_path), width="stretch")
        return
    safe_label = html.escape(label)
    st.markdown(
        f'<div class="sprite-placeholder {role}-sprite">{safe_label}<br>SPRITE SLOT</div>',
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def image_data_uri(path_string: str) -> str:
    encoded = base64.b64encode(Path(path_string).read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def render_tower() -> None:
    image_path = ASSET_DIR / "tower_intro.png"
    if image_path.exists():
        st.image(str(image_path), width="stretch")
        return
    st.markdown('<div class="tower-frame">담합의 탑<br>5F BATTLE QUEST</div>', unsafe_allow_html=True)


def current_elapsed() -> int:
    started_at = st.session_state.main_started_at
    if not started_at:
        return 0
    return max(0, int(time.time() - started_at))


def render_hud(floor_number: int, scene_number: int) -> None:
    st.markdown(
        "<div class='hud'>"
        f"<span class='hud-chip'>FLOOR {floor_number}/5</span>"
        f"<span class='hud-chip'>장면 {scene_number}/3</span>"
        f"<span class='hud-chip'>시간 {seconds_text(current_elapsed())}</span>"
        f"<span class='hud-chip'>위험 선택 {'사용함' if st.session_state.risk_used else '1회 가능'}</span>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_battle(floor: dict) -> None:
    background_path = ASSET_DIR / f"battle_bg_floor_{floor['number']}.png"
    if floor["number"] <= 4 and not background_path.exists():
        background_path = ASSET_DIR / "battle_bg_floor_1.png"
    enemy_path = ASSET_DIR / floor["asset"]
    hero_path = ASSET_DIR / "hero_male_back.png"

    if background_path.exists():
        background_uri = image_data_uri(str(background_path))
        enemy_markup = ""
        if enemy_path.exists():
            enemy_uri = image_data_uri(str(enemy_path))
            enemy_name = html.escape(floor["enemy"])
            enemy_markup = f'<img class="battle-sprite battle-enemy" src="{enemy_uri}" alt="{enemy_name}">'
        hero_markup = ""
        if hero_path.exists():
            hero_uri = image_data_uri(str(hero_path))
            hero_markup = f'<img class="battle-sprite battle-hero" src="{hero_uri}" alt="플레이어 캐릭터">'

        enemy_name = html.escape(floor["enemy"])
        team_name = html.escape(floor["team"])
        arena_markup = (
            f'<div class="battle-arena" style="background-image: url(\'{background_uri}\');">'
            '<div class="battle-status battle-status-enemy">'
            f'<div class="battle-name">{enemy_name}</div>'
            f'<div class="battle-role">{team_name} 구역</div>'
            '<div class="hp-track enemy-hp"><div class="hp-fill"></div></div>'
            '</div>'
            f'{enemy_markup}'
            f'{hero_markup}'
            '<div class="battle-status battle-status-player">'
            '<div class="battle-name">플레이어</div>'
            '<div class="battle-role">전략의 수호자</div>'
            '<div class="hp-track"><div class="hp-fill"></div></div>'
            '</div>'
            '</div>'
        )
        st.markdown(arena_markup, unsafe_allow_html=True)
        return

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("<div class='battle-name'>플레이어</div><div class='battle-role'>전략의 수호자</div>", unsafe_allow_html=True)
        st.markdown("<div class='hp-track'><div class='hp-fill'></div></div>", unsafe_allow_html=True)
        render_sprite("hero_male_back.png", "전략의 수호자", "hero")
    with right:
        st.markdown(
            f"<div class='battle-name'>{html.escape(floor['enemy'])}</div><div class='battle-role'>{html.escape(floor['team'])} 구역</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div class='hp-track enemy-hp'><div class='hp-fill'></div></div>", unsafe_allow_html=True)
        render_sprite(floor["asset"], floor["enemy"], "enemy")


def choose_main_option(floor: dict, scene: dict, option: dict) -> None:
    awarded_score = option["score"]
    risk_success = None
    feedback = option["feedback"]

    if option["kind"] == "risk":
        st.session_state.risk_used = True
        risk_success = random.randrange(100) < option["chance"]
        st.session_state.risk_success = risk_success
        if risk_success:
            awarded_score = option["reward"]
            feedback = (
                f"기적처럼 이번에는 감시망을 피했습니다. +{awarded_score}점. "
                "하지만 결과가 좋았다고 선택이 정당화되지는 않습니다. 실제 업무에서는 절대 기대면 안 되는 길입니다."
            )
        else:
            awarded_score = 0
            feedback = option["worst"]

    st.session_state.selections.append(
        {
            "floor": floor["number"],
            "scene": scene["title"],
            "choice_key": option["key"],
            "choice_text": option["text"],
            "kind": option["kind"],
            "initial_score": option["score"],
            "base_score": awarded_score,
            "followup_key": None,
            "followup_text": None,
            "followup_score": None,
            "followup_feedback": None,
            "score": awarded_score,
            "risk_success": risk_success,
            "feedback": feedback,
            "best": scene["best"],
            "memory": scene.get("memory", ""),
            "recommended_followup": scene.get("recommended_followup", ""),
        }
    )
    st.session_state.main_score += awarded_score
    st.session_state.pending_followup = len(st.session_state.selections) - 1
    st.rerun()


def choose_followup(floor: dict, scene: dict, option: dict) -> None:
    result_index = st.session_state.pending_followup
    if result_index is None:
        return

    result = st.session_state.selections[result_index]
    result["followup_key"] = option["key"]
    result["followup_text"] = option["text"]
    result["followup_score"] = option["score"]
    result["followup_feedback"] = option["feedback"]
    result["score"] += option["score"]
    st.session_state.main_score += option["score"]
    st.session_state.pending_followup = None

    if st.session_state.scene_index == len(floor["scenes"]) - 1:
        if st.session_state.floor_index == len(FLOORS) - 1:
            st.session_state.main_seconds = current_elapsed()
        st.session_state.show_floor_feedback = True
    else:
        st.session_state.scene_index += 1
    st.rerun()


def render_floor_feedback() -> None:
    floor = FLOORS[st.session_state.floor_index]
    results = [result for result in st.session_state.selections if result["floor"] == floor["number"]]
    floor_score = sum(result["score"] for result in results)

    if st.session_state.floor_index == len(FLOORS) - 1:
        button_label = "본편 결과 확인"
    else:
        button_label = f"{floor['number'] + 1}층으로 이동"

    with st.container(key="floor_feedback_parchment"):
        st.markdown(
            f"<h1 class='parchment-title'>{floor['number']}층 결산</h1>"
            "<div class='parchment-rule'></div>"
            f"<p class='parchment-closing'>{html.escape(floor['closing'])}</p>",
            unsafe_allow_html=True,
        )
        metrics = st.columns(3)
        metrics[0].metric("이번 층 점수", f"{floor_score}점")
        metrics[1].metric("누적 점수", f"{st.session_state.main_score}점")
        metrics[2].metric("선택 장면", f"{len(results)}개")

        lesson_items = "".join(f"<li>{html.escape(lesson)}</li>" for lesson in floor.get("lessons", []))
        if lesson_items:
            st.markdown(
                "<div class='parchment-lessons'><strong>이번 층의 핵심</strong>"
                f"<ul>{lesson_items}</ul></div>",
                unsafe_allow_html=True,
            )

        terms = floor.get("terms", {})
        if terms:
            term_items = "".join(f"<li>{html.escape(term)}</li>" for term in terms)
            st.markdown(
                "<div class='parchment-terms'><strong>낯선 말 풀어보기</strong>"
                f"<ul>{term_items}</ul></div>",
                unsafe_allow_html=True,
            )

        for index, result in enumerate(results, start=1):
            risk_class = "risk" if result["kind"] == "risk" else "good"
            if result["kind"] == "risk":
                base_label = "위험 선택 보상" if result["risk_success"] else "위험 선택"
            else:
                base_label = "1차 판단"
            st.markdown(
                f"<div class='parchment-result'>"
                f"<div class='parchment-result-title {risk_class}'>{index}. {html.escape(result['scene'])} · {result['score']}점</div>"
                f"<p class='parchment-score'>{base_label} {result['base_score']}점 + 후속 조치 {result['followup_score']}점</p>"
                f"<p class='parchment-memory'>한 줄 원칙 · {html.escape(result['memory'])}</p>"
                "<details class='parchment-review'>"
                "<summary>내 선택과 자세한 해설 보기</summary>"
                "<p class='review-label'>내가 고른 1차 판단</p>"
                f"<p class='review-choice'>{html.escape(result['choice_text'])}</p>"
                "<p class='review-label'>1차 판단 해설</p>"
                f"<p class='review-choice'>{html.escape(result['feedback'])}</p>"
                "<p class='review-label'>내가 고른 후속 조치</p>"
                f"<p class='review-choice'>{html.escape(result['followup_text'] or '선택하지 않음')}</p>"
                "<p class='review-label'>후속 조치 해설</p>"
                f"<p class='review-choice'>{html.escape(result['followup_feedback'] or '후속 조치가 선택되지 않았습니다.')}</p>"
                "<p class='review-label'>실무에서 권장되는 1차 대응</p>"
                f"<p class='parchment-best'>{html.escape(result['best'])}</p>"
                "<p class='review-label'>권장 후속 조치</p>"
                f"<p class='parchment-best'>{html.escape(result['recommended_followup'])}</p>"
                "</details>"
                "</div>",
                unsafe_allow_html=True,
            )

        _, action_column = st.columns([3, 2])
        with action_column:
            if st.button(button_label, width="stretch", key="next_floor"):
                st.session_state.show_floor_feedback = False
                if st.session_state.floor_index == len(FLOORS) - 1:
                    st.session_state.page = "main_result"
                else:
                    st.session_state.floor_index += 1
                    st.session_state.scene_index = 0
                st.rerun()


def render_main_game() -> None:
    if st.session_state.show_floor_feedback:
        render_floor_feedback()
        return

    floor = FLOORS[st.session_state.floor_index]
    scene = floor["scenes"][st.session_state.scene_index]
    render_hud(floor["number"], st.session_state.scene_index + 1)
    st.progress((st.session_state.floor_index * 3 + st.session_state.scene_index) / TOTAL_SCENES)
    st.title(f"{floor['number']}층 · {floor['title']}")
    st.caption(floor["opening"])
    render_battle(floor)
    st.markdown(
        "<div class='pixel-panel'><div class='encounter-label'>적의 제안</div>"
        f"<h3>{html.escape(scene['title'])}</h3>"
        f"<p class='dialogue'>{html.escape(scene['situation'])}</p></div>",
        unsafe_allow_html=True,
    )
    pending_index = st.session_state.pending_followup
    if pending_index is not None:
        result = st.session_state.selections[pending_index]
        st.markdown(
            "<div class='pixel-panel'>"
            "<div class='followup-step'>2차 선택 · 후속 조치</div>"
            "<h3>추가적으로 진행할 사항이 있습니까?</h3>"
            f"<p class='dialogue'>{html.escape(result['feedback'])}</p>"
            "<p class='dialogue'>현장 판단 이후 회사 차원에서 이어갈 행동을 선택하십시오.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        followup_options = shuffled_scene_options(
            floor["number"], st.session_state.scene_index, scene, "followups"
        )
        for option in followup_options:
            if st.button(
                option["text"],
                key=f"followup_{floor['number']}_{st.session_state.scene_index}_{option['key']}",
                width="stretch",
            ):
                choose_followup(floor, scene, option)
        return

    st.markdown(
        "<p class='danger-note'>1차 판단과 후속 조치의 일반 점수는 공개되지 않습니다. 본편의 위험 선택은 단 한 번만 사용할 수 있습니다.</p>",
        unsafe_allow_html=True,
    )

    main_options = shuffled_scene_options(
        floor["number"], st.session_state.scene_index, scene, "choices"
    )
    for option in main_options:
        is_risk = option["kind"] == "risk"
        disabled = is_risk and st.session_state.risk_used
        label = option["text"]
        if is_risk:
            suffix = "이미 사용함" if disabled else f"위험 선택 · 성공 확률 {option['chance']}% · 성공 시 +{option['reward']}점"
            label = f"{label}\n[{suffix}]"
        if st.button(
            label,
            key=f"choice_{floor['number']}_{st.session_state.scene_index}_{option['key']}",
            width="stretch",
            disabled=disabled,
        ):
            choose_main_option(floor, scene, option)


def main_title_and_feedback() -> tuple[str, list[str]]:
    score = st.session_state.main_score
    ordinary = [result for result in st.session_state.selections if result["kind"] == "normal"]
    perfect_responses = sum(
        result["initial_score"] == 80 and result["followup_score"] == 20 for result in ordinary
    )
    incomplete_followups = sum((result["followup_score"] or 0) < 20 for result in ordinary)
    weak_initial_judgments = sum(result["initial_score"] <= 40 for result in ordinary)
    notes: list[str] = []

    if score >= 1350:
        title = "공정거래 수호자"
        notes.append("가격·물량·고객·입찰 조건의 위험 신호를 빠르게 구분했고, 대화를 끊은 뒤 원본 보존과 독립적인 재검토까지 연결했습니다.")
    elif score >= 1100:
        title = "원칙 설계자"
        notes.append("핵심 원칙은 지켰습니다. 이제는 거절에서 끝내지 말고 원본 보존, 확산 차단, 영향을 받은 자료의 재검토까지 이어가 보세요.")
    elif score >= 800:
        title = "경계선 감지자"
        notes.append("명백한 위험은 피했지만, 대화 이탈·원본 보존·영향 자료 재검토 중 일부가 빠졌습니다.")
    else:
        title = "회색지대 탐험가"
        notes.append("성과 압박이나 관계 관리의 언어가 나와도 경쟁 민감정보의 교환과 활용은 선을 그어야 합니다.")

    if incomplete_followups:
        notes.append(
            f"{incomplete_followups}개 장면에서 후속 조치가 완결되지 않았습니다. "
            "보고 여부만이 아니라 원본 보존, 확산 차단, 영향을 받은 자료의 재검토, 적절한 이관 경로까지 함께 확인해야 합니다."
        )
    if weak_initial_judgments:
        notes.append(f"{weak_initial_judgments}개 장면에서 위험한 대화나 자료에 불필요하게 노출됐습니다. 후속 보고가 있더라도 최초 대응에서 즉시 중단·이탈하는 판단이 먼저 필요합니다.")
    if st.session_state.risk_used and st.session_state.risk_success:
        notes.append("위험 선택은 운 좋게 통과해 점수를 얻었지만, 한 번이라도 위험 선택을 사용했으므로 공정의 검의 선택은 받을 수 없습니다.")
    if st.session_state.risk_used and not st.session_state.risk_success:
        notes.append("위험 선택이 실패했습니다. 결과와 관계없이 한 번이라도 위험 선택을 사용하면 공정의 검의 선택은 받을 수 없습니다.")
    if perfect_responses >= 10:
        notes.append("특히 독립적 의사결정의 원칙과 대체 가능한 업무 경로를 함께 제시한 점이 강점입니다.")
    return title, notes


def render_main_result() -> None:
    title, notes = main_title_and_feedback()
    st.title("본편 돌파 결과")
    sword_denied = st.session_state.risk_used
    ending_path = ASSET_DIR / ("hero_male_sword_rejected.png" if sword_denied else "hero_male_front_sword.png")
    if ending_path.exists():
        ending_uri = image_data_uri(str(ending_path))
        if sword_denied:
            scene_class = "ending-scene denied"
            hero_class = "ending-hero denied"
            hero_alt = "공정의 검을 뽑지 못한 플레이어"
            kicker = "TOWER CLEARED · SWORD REJECTED"
            ending_title = "게임은 클리어했으나<br>공정의 검의 선택은 받지 못했습니다"
            ending_message = (
                f"{title} 칭호와 획득 점수는 기록됩니다. 하지만 확률성 위험 선택은 성공 여부와 관계없이 "
                "공정의 검 획득 조건을 잃게 합니다."
            )
        else:
            scene_class = "ending-scene"
            hero_class = "ending-hero"
            hero_alt = "공정의 검을 든 플레이어"
            kicker = "TOWER CLEARED"
            ending_title = "마왕을 무찌르고<br>공정의 검을 획득했습니다"
            ending_message = (
                f"{title} 칭호를 획득했습니다. 실제 업무에서도 위험한 대화는 즉시 중단하고, "
                "기록과 보고까지 이어가세요."
            )
        st.markdown(
            f"<div class='{scene_class}'>"
            f"<img class='{hero_class}' src='{ending_uri}' alt='{hero_alt}'>"
            "<div class='ending-copy'>"
            f"<div class='ending-kicker'>{kicker}</div>"
            f"<div class='ending-title{' denied' if sword_denied else ''}'>{ending_title}</div>"
            f"<p class='ending-message'>{html.escape(ending_message)}</p>"
            "</div></div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div class='pixel-panel'><h2>{html.escape(title)}</h2>"
            "<p class='dialogue'>담합의 탑 본편을 돌파했습니다. 점수만큼 중요한 것은, 실제 상황에서 위험한 대화의 경계를 인식하고 중단·기록·보고까지 실행하는 것입니다.</p></div>",
            unsafe_allow_html=True,
        )
    metrics = st.columns(3)
    metrics[0].metric("본편 점수", f"{st.session_state.main_score}점")
    metrics[1].metric("본편 시간", seconds_text(st.session_state.main_seconds))
    metrics[2].metric("위험 선택", "성공" if st.session_state.risk_success else "미사용" if not st.session_state.risk_used else "실패")

    for note in notes:
        st.markdown(f"<div class='pixel-panel'><p class='dialogue'>{html.escape(note)}</p></div>", unsafe_allow_html=True)

    left, right = st.columns(2)
    with left:
        if st.button("마왕에게 도전한다", width="stretch", key="start_bonus"):
            st.session_state.page = "bonus"
            st.rerun()
    with right:
        if st.button("본편 기록 확정", width="stretch", key="finish_main"):
            st.session_state.page = "final"
            st.rerun()


def current_bonus_challenge() -> tuple[dict, int, int]:
    attempts = st.session_state.bonus_attempts
    challenge = BOSS_CHALLENGES[attempts % len(BOSS_CHALLENGES)]
    round_number = attempts // len(BOSS_CHALLENGES) + 1
    reward = challenge["reward"] + (round_number - 1) * 50
    return challenge, round_number, reward


def bonus_success_rate(attempts: int) -> int:
    return BONUS_SUCCESS_RATES[min(attempts, len(BONUS_SUCCESS_RATES) - 1)]


def choose_bonus_challenge() -> None:
    challenge, round_number, reward = current_bonus_challenge()
    success_rate = bonus_success_rate(st.session_state.bonus_attempts)
    success = random.randrange(100) < success_rate
    st.session_state.bonus_attempts += 1
    if success:
        st.session_state.bonus_streak += 1
        st.session_state.bonus_score += reward
        st.session_state.bonus_result = {
            "success": True,
            "title": challenge["title"],
            "message": f"기적 발생. {reward}점 획득. 하지만 이 선택은 현실에서 가장 피해야 할 선택입니다.",
            "round": round_number,
        }
    else:
        st.session_state.bonus_result = {
            "success": False,
            "title": challenge["title"],
            "message": challenge["worst"],
            "round": round_number,
        }
    st.session_state.page = "bonus_outcome"
    st.rerun()


def render_bonus() -> None:
    challenge, round_number, reward = current_bonus_challenge()
    success_rate = bonus_success_rate(st.session_state.bonus_attempts)
    st.title("번외 · 마왕에게 도전")
    st.markdown(
        "<div class='pixel-panel'><p class='dialogue'>"
        "여기는 점수 경쟁을 위한 번외 구역입니다. 실제 업무에서 절대 선택하면 안 되는 길만 고릅니다. "
        "성공 확률은 첫 도전 50%, 두 번째 30%, 세 번째 20%, 네 번째 10%, 다섯 번째 이후 5%입니다. "
        "실패하면 그 선택의 최악의 결과를 확인하고 종료합니다."
        "</p></div>",
        unsafe_allow_html=True,
    )
    metrics = st.columns(3)
    metrics[0].metric("번외 점수", f"{st.session_state.bonus_score}점")
    metrics[1].metric("연속 통과", f"{st.session_state.bonus_streak}회")
    metrics[2].metric("심연 회차", f"{round_number}회차")
    render_battle(FLOORS[-1])
    st.markdown(
        f"<div class='pixel-panel'><h3>{html.escape(challenge['title'])}</h3>"
        f"<p class='dialogue'>{html.escape(challenge['situation'])}</p>"
        f"<p class='feedback-risk'>성공 확률 {success_rate}% · 성공 시 +{reward}점</p></div>",
        unsafe_allow_html=True,
    )
    if st.button(challenge["action"], width="stretch", key="take_bonus_risk"):
        choose_bonus_challenge()
    if st.button("여기서 물러나고 기록 확정", width="stretch", key="end_bonus"):
        st.session_state.page = "final"
        st.rerun()


def render_bonus_outcome() -> None:
    outcome = st.session_state.bonus_result
    if not outcome:
        st.session_state.page = "bonus"
        st.rerun()
        return
    st.title("마왕의 판정")
    style = "feedback-good" if outcome["success"] else "feedback-risk"
    headline = "통과" if outcome["success"] else "패배"
    st.markdown(
        f"<div class='pixel-panel'><h2 class='{style}'>{headline}</h2>"
        f"<p class='dialogue'>{html.escape(outcome['message'])}</p></div>",
        unsafe_allow_html=True,
    )
    metrics = st.columns(2)
    metrics[0].metric("번외 점수", f"{st.session_state.bonus_score}점")
    metrics[1].metric("연속 통과", f"{st.session_state.bonus_streak}회")

    if outcome["success"]:
        left, right = st.columns(2)
        with left:
            if st.button("더 깊이 내려간다", width="stretch", key="continue_bonus"):
                st.session_state.page = "bonus"
                st.rerun()
        with right:
            if st.button("번외 기록 확정", width="stretch", key="finish_after_success"):
                st.session_state.page = "final"
                st.rerun()
    elif st.button("기록 확정", width="stretch", key="finish_after_failure"):
        st.session_state.page = "final"
        st.rerun()


def build_result_payload() -> dict:
    if not st.session_state.record_code:
        st.session_state.record_code = f"TOWER-{uuid.uuid4().hex[:8].upper()}"
    choices = " | ".join(
        f"{result['floor']}층-{result['scene']}:{result['score']}점"
        f"(1차 {result['base_score']}+후속 {result['followup_score']})"
        for result in st.session_state.selections
    )
    return {
        "record_code": st.session_state.record_code,
        "name": st.session_state.player["name"],
        "department": st.session_state.player["department"],
        "main_score": st.session_state.main_score,
        "main_seconds": st.session_state.main_seconds or 0,
        "bonus_score": st.session_state.bonus_score,
        "bonus_streak": st.session_state.bonus_streak,
        "bonus_attempts": st.session_state.bonus_attempts,
        "main_risk_used": "Y" if st.session_state.risk_used else "N",
        "main_risk_success": "Y" if st.session_state.risk_success else "N",
        "main_choices": choices,
    }


def render_final() -> None:
    payload = build_result_payload()
    st.title("기록의 방")
    st.markdown(
        f"<div class='pixel-panel'><h2>{html.escape(st.session_state.player['name'])} 님의 원정 기록</h2>"
        "<p class='dialogue'>본편 순위는 본편 점수 우선, 동점 시 플레이 시간 순으로 확인합니다. 번외는 번외 점수와 연속 통과 기록으로 별도 집계합니다.</p></div>",
        unsafe_allow_html=True,
    )
    metrics = st.columns(4)
    metrics[0].metric("본편", f"{payload['main_score']}점")
    metrics[1].metric("시간", seconds_text(payload["main_seconds"]))
    metrics[2].metric("번외", f"{payload['bonus_score']}점")
    metrics[3].metric("연속 통과", f"{payload['bonus_streak']}회")
    st.caption(f"기록 코드: {payload['record_code']}")

    if st.session_state.submission_status is True:
        st.success(st.session_state.submission_message)
    else:
        if st.session_state.submission_status is False:
            st.error(st.session_state.submission_message)
        if st.button("Google Sheets에 기록하기", width="stretch", key="submit_result"):
            try:
                success, message = append_result(st.secrets, payload)
            except Exception:
                success, message = False, "Google Sheets 시크릿이 아직 설정되지 않았습니다. README의 설정 예시를 확인해 주세요."
            st.session_state.submission_status = success
            st.session_state.submission_message = message
            st.rerun()

    if st.button("새 도전자 시작", width="stretch", key="new_game"):
        reset_game()
        st.rerun()


def render_landing() -> None:
    render_tower()
    st.caption("전략기획 · 전략투자 · 브랜드성장 컴플라이언스 배틀")
    st.markdown(
        "<div class='pixel-panel'><p class='dialogue'>"
        "5개 층, 15개의 실제 업무형 장면. 점수보다 먼저, 위험한 신호를 멈추고 기록하며 보고하는 판단을 시험합니다. "
        "본편의 위험 선택은 단 한 번뿐입니다."
        "</p></div>",
        unsafe_allow_html=True,
    )
    name = st.text_input("이름", max_chars=30, key="player_name", placeholder="이름을 입력하세요")
    department = st.selectbox("부서", DEPARTMENTS, key="player_department")
    if st.button("탑에 입장", width="stretch", key="start_game"):
        clean_name = name.strip()
        if not clean_name:
            st.warning("이름을 입력해 주세요.")
        else:
            st.session_state.player = {"name": clean_name, "department": department}
            st.session_state.main_started_at = time.time()
            st.session_state.page = "main_game"
            st.rerun()


def main() -> None:
    apply_style()
    init_state()
    page = st.session_state.page
    if page == "landing":
        render_landing()
    elif page == "main_game":
        render_main_game()
    elif page == "main_result":
        render_main_result()
    elif page == "bonus":
        render_bonus()
    elif page == "bonus_outcome":
        render_bonus_outcome()
    elif page == "final":
        render_final()
    else:
        reset_game()
        st.rerun()


if __name__ == "__main__":
    main()
