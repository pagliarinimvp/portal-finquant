"use strict";
{
    function setTheme(mode) {
        if (mode !== "light" && mode !== "dark") {
            mode = "light";
        }
        document.documentElement.dataset.theme = mode;
        localStorage.setItem("theme", mode);
    }

    function cycleTheme() {
        const currentTheme = localStorage.getItem("theme") || "light";
        setTheme(currentTheme === "dark" ? "light" : "dark");
    }

    function initTheme() {
        // usa o tema salvo, ou o preferido pelo sistema como ponto de partida
        const currentTheme = localStorage.getItem("theme");
        if (currentTheme) {
            setTheme(currentTheme);
        } else {
            const prefersDark = window.matchMedia(
                "(prefers-color-scheme: dark)",
            ).matches;
            setTheme(prefersDark ? "dark" : "light");
        }
    }

    window.addEventListener("load", function (_) {
        const buttons = document.getElementsByClassName("theme-toggle");
        Array.from(buttons).forEach((btn) => {
            btn.addEventListener("click", cycleTheme);
        });
    });

    initTheme();
}
