import streamlit as st


# ============================================================
# ECDAT
# Enterprise Cryptographic Discovery & Analysis Tool
#
# Phase 1.1
# Visual Foundation / Landing Screen
# ============================================================


st.set_page_config(
    page_title="ECDAT",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# LANDING PAGE
# ============================================================

landing_page = """
<style>

    /* ========================================================
       ECDAT DESIGN TOKENS
       ======================================================== */

    :root {
        --ecdat-bg: #0E1522;

        --ecdat-yellow: #F4C430;
        --ecdat-yellow-bright: #FFD84D;

        --ecdat-white: #F5F7FA;
        --ecdat-muted: #8E9AAA;

        --ecdat-dot: rgba(255, 255, 255, 0.12);
    }


    /* ========================================================
       STREAMLIT RESET
       ======================================================== */

    html,
    body {
        margin: 0;
        padding: 0;

        background:
            var(--ecdat-bg);
    }


    [data-testid="stAppViewContainer"] {
        background:
            var(--ecdat-bg);
    }


    [data-testid="stHeader"] {
        background:
            transparent;
    }


    .block-container {
        max-width: none !important;

        padding-top: 0 !important;
        padding-bottom: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
    }


    #MainMenu {
        visibility: hidden;
    }


    footer {
        visibility: hidden;
    }


    /* ========================================================
       ENTRY SCREEN
       ======================================================== */

    .ecdat-entry {

        position: relative;

        width: 100%;

        min-height: 100vh;

        overflow: hidden;

        display: flex;

        align-items: center;

        justify-content: center;

        background:
            radial-gradient(
                circle at 50% 46%,
                rgba(244, 196, 48, 0.045),
                transparent 38%
            ),

            var(--ecdat-bg);
    }


    /* ========================================================
       DOT FIELD
       ======================================================== */

    .ecdat-grid {

        position: absolute;

        top: -15%;
        left: -15%;

        width: 130%;
        height: 130%;

        pointer-events: none;

        opacity: 0.85;

        background-image:

            radial-gradient(
                circle,
                var(--ecdat-dot) 1px,
                transparent 1.5px
            );

        background-size:
            28px 28px;

        animation:
            ecdat-grid-breathe
            12s
            ease-in-out
            infinite
            alternate;
    }


    /* ========================================================
       GRID MOTION
       ======================================================== */

    @keyframes ecdat-grid-breathe {

        0% {

            transform:
                translate3d(
                    -0.8%,
                    -0.4%,
                    0
                )
                scale(1);
        }


        50% {

            transform:
                translate3d(
                    0.4%,
                    0.6%,
                    0
                )
                scale(1.012);
        }


        100% {

            transform:
                translate3d(
                    0.8%,
                    -0.2%,
                    0
                )
                scale(1.02);
        }
    }


    /* ========================================================
       YELLOW ATMOSPHERIC LIGHT
       ======================================================== */

    .ecdat-glow {

        position: absolute;

        width: 620px;
        height: 620px;

        border-radius: 50%;

        background:

            radial-gradient(
                circle,

                rgba(
                    244,
                    196,
                    48,
                    0.075
                ) 0%,

                rgba(
                    244,
                    196,
                    48,
                    0.025
                ) 35%,

                transparent 70%
            );

        filter:
            blur(85px);

        pointer-events: none;
    }


    /* ========================================================
       HERO CONTENT
       ======================================================== */

    .ecdat-content {

        position: relative;

        z-index: 5;

        width:
            min(
                960px,
                90vw
            );

        padding:
            60px 32px;

        text-align:
            center;
    }


    /* ========================================================
       TECHNICAL KICKER
       ======================================================== */

    .ecdat-kicker {

        margin-bottom:
            28px;

        font-family:
            "JetBrains Mono",
            monospace;

        font-size:
            11px;

        font-weight:
            500;

        line-height:
            1.5;

        letter-spacing:
            0.18em;

        text-transform:
            uppercase;

        color:
            var(--ecdat-yellow);
    }


    /* ========================================================
       ECDAT LOGOTYPE
       ======================================================== */

    .ecdat-title {

        margin:
            0;

        font-family:
            "Space Grotesk",
            sans-serif;

        font-size:
            clamp(
                72px,
                10vw,
                128px
            );

        font-weight:
            600;

        line-height:
            0.84;

        letter-spacing:
            -0.075em;

        color:
            var(--ecdat-white);
    }


    /* ========================================================
       PRODUCT LINE
       ======================================================== */

    .ecdat-subtitle {

        margin-top:
            34px;

        font-family:
            "Space Grotesk",
            sans-serif;

        font-size:
            clamp(
                22px,
                3vw,
                38px
            );

        font-weight:
            400;

        line-height:
            1.18;

        letter-spacing:
            -0.035em;

        color:
            var(--ecdat-white);
    }


    /* ========================================================
       EDITORIAL SERIF
       ======================================================== */

    .ecdat-serif {

        font-family:
            "Noto Serif",
            serif;

        font-style:
            italic;

        font-weight:
            400;

        color:
            var(--ecdat-yellow);
    }


    /* ========================================================
       DESCRIPTION
       ======================================================== */

    .ecdat-description {

        max-width:
            620px;

        margin:
            28px auto 0;

        font-family:
            "Space Grotesk",
            sans-serif;

        font-size:
            15px;

        font-weight:
            400;

        line-height:
            1.7;

        letter-spacing:
            0.005em;

        color:
            var(--ecdat-muted);
    }


    /* ========================================================
       ENTER BUTTON
       ======================================================== */

    .ecdat-button {

        display:
            inline-flex;

        align-items:
            center;

        justify-content:
            center;

        min-width:
            178px;

        margin-top:
            42px;

        padding:
            15px 24px;

        border:
            1px solid
            rgba(
                244,
                196,
                48,
                0.9
            );

        border-radius:
            6px;

        background:
            var(--ecdat-yellow);

        color:
            var(--ecdat-bg);

        font-family:
            "JetBrains Mono",
            monospace;

        font-size:
            12px;

        font-weight:
            600;

        line-height:
            1;

        letter-spacing:
            0.035em;

        text-decoration:
            none;

        transition:
            transform 180ms ease,
            background 180ms ease,
            box-shadow 180ms ease;
    }


    /* ========================================================
       BUTTON HOVER
       ======================================================== */

    .ecdat-button:hover {

        background:
            var(--ecdat-yellow-bright);

        color:
            var(--ecdat-bg);

        transform:
            translateY(-2px);

        box-shadow:
            0 12px 36px
            rgba(
                244,
                196,
                48,
                0.15
            );
    }


    .ecdat-button:active {

        transform:
            translateY(0);
    }


    /* ========================================================
       DIVIDER
       ======================================================== */

    .ecdat-line {

        width:
            42px;

        height:
            1px;

        margin:
            24px auto 0;

        background:
            rgba(
                244,
                196,
                48,
                0.6
            );
    }


    /* ========================================================
       TECHNICAL FOOTER TEXT
       ======================================================== */

    .ecdat-meta {

        margin-top:
            27px;

        font-family:
            "JetBrains Mono",
            monospace;

        font-size:
            10px;

        font-weight:
            400;

        line-height:
            1.5;

        letter-spacing:
            0.11em;

        text-transform:
            uppercase;

        color:
            rgba(
                142,
                154,
                170,
                0.72
            );
    }


    /* ========================================================
       REDUCED MOTION
       ======================================================== */

    @media (
        prefers-reduced-motion: reduce
    ) {

        .ecdat-grid {

            animation:
                none;
        }

        .ecdat-button {

            transition:
                none;
        }
    }


    /* ========================================================
       MOBILE
       ======================================================== */

    @media (
        max-width: 700px
    ) {

        .ecdat-content {

            width:
                92vw;

            padding:
                50px 20px;
        }


        .ecdat-title {

            font-size:
                clamp(
                    64px,
                    19vw,
                    100px
                );
        }


        .ecdat-subtitle {

            font-size:
                24px;
        }


        .ecdat-description {

            font-size:
                14px;
        }


        .ecdat-meta {

            font-size:
                9px;

            letter-spacing:
                0.08em;
        }
    }

</style>


<!-- ============================================================
     ECDAT ENTRY
     ============================================================ -->

<main class="ecdat-entry">


    <!-- ========================================================
         AMBIENT DOT FIELD
         ======================================================== -->

    <div
        class="ecdat-grid"
        aria-hidden="true">
    </div>


    <!-- ========================================================
         YELLOW ATMOSPHERE
         ======================================================== -->

    <div
        class="ecdat-glow"
        aria-hidden="true">
    </div>


    <!-- ========================================================
         HERO CONTENT
         ======================================================== -->

    <section class="ecdat-content">


        <!-- Project metadata -->

        <div class="ecdat-kicker">

            SIH26-26164
            &nbsp;&nbsp;/&nbsp;&nbsp;
            NTRO
            &nbsp;&nbsp;/&nbsp;&nbsp;
            PROTOTYPE

        </div>


        <!-- Product name -->

        <h1 class="ecdat-title">

            ECDAT

        </h1>


        <!-- Product descriptor -->

        <div class="ecdat-subtitle">

            Enterprise Cryptographic

            <span class="ecdat-serif">

                Discovery &amp; Analysis

            </span>

        </div>


        <!-- Product statement -->

        <div class="ecdat-description">

            Discover cryptographic usage.
            Trace evidence.
            Assess quantum exposure.
            Plan migration.

        </div>


        <!-- Primary action -->

        <a
            class="ecdat-button"
            href="?page=overview">

            ENTER ECDAT
            &nbsp;&nbsp;→

        </a>


        <!-- Small brand divider -->

        <div class="ecdat-line"></div>


        <!-- Technical positioning -->

        <div class="ecdat-meta">

            CRYPTOGRAPHIC VISIBILITY
            &nbsp;/&nbsp;
            POST-QUANTUM READINESS

        </div>


    </section>

</main>
"""


# ============================================================
# RENDER
# ============================================================

st.html(landing_page)
