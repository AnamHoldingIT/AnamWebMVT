// zlink.js

document.addEventListener("DOMContentLoaded", () => {

    /* ============================================================
       1) BACKGROUND — NEURAL NETWORK + QUANTUM DUST
       ============================================================ */

    const neuralCanvas = document.getElementById("neural-layer");
    const dustCanvas = document.getElementById("quantum-dust");

    let nctx = null;
    let dctx = null;

    if (neuralCanvas && dustCanvas) {
        nctx = neuralCanvas.getContext("2d");
        dctx = dustCanvas.getContext("2d");
    }

    let w = window.innerWidth;
    let h = window.innerHeight;

    function resize() {
        w = window.innerWidth;
        h = window.innerHeight;

        if (neuralCanvas && dustCanvas) {
            neuralCanvas.width = dustCanvas.width = w;
            neuralCanvas.height = dustCanvas.height = h;
        }
    }

    resize();
    window.addEventListener("resize", resize);

    // --- Neural nodes ---
    const NODE_COUNT = 90;
    let nodes = [];
    const mouse = { x: null, y: null };

    function initNodes() {
        nodes = [];
        for (let i = 0; i < NODE_COUNT; i++) {
            nodes.push({
                x: Math.random() * w,
                y: Math.random() * h,
                vx: (Math.random() - 0.5) * 0.4,
                vy: (Math.random() - 0.5) * 0.4,
                s: Math.random() * 2 + 1.2
            });
        }
    }

    // --- Quantum dust ---
    const DUST_COUNT = 60;
    let dusts = [];

    function initDust() {
        dusts = [];
        for (let i = 0; i < DUST_COUNT; i++) {
            dusts.push({
                x: Math.random() * w,
                y: Math.random() * h,
                vx: (Math.random() - 0.5) * 0.15,
                vy: (Math.random() - 0.5) * 0.15,
                s: Math.random() * 1.4 + 0.5
            });
        }
    }

    if (nctx && dctx) {
        initNodes();
        initDust();
    }

    window.addEventListener("mousemove", e => {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
    });

    window.addEventListener("mouseleave", () => {
        mouse.x = mouse.y = null;
    });

    function drawNeural() {
        if (!nctx) return;

        nctx.clearRect(0, 0, w, h);

        nodes.forEach((n1, i) => {
            n1.x += n1.vx;
            n1.y += n1.vy;

            if (n1.x < 0 || n1.x > w) n1.vx *= -1;
            if (n1.y < 0 || n1.y > h) n1.vy *= -1;

            if (mouse.x !== null && mouse.y !== null) {
                const dx = n1.x - mouse.x;
                const dy = n1.y - mouse.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                const influenceRadius = 140;
                const power = 0.25;

                if (dist < influenceRadius) {
                    const force = (influenceRadius - dist) / influenceRadius * power;
                    n1.x += dx * force;
                    n1.y += dy * force;
                }
            }

            // Node
            nctx.beginPath();
            nctx.arc(n1.x, n1.y, n1.s, 0, Math.PI * 2);
            nctx.fillStyle = "rgba(0,255,255,0.9)";
            nctx.shadowColor = "rgba(0,255,255,0.7)";
            nctx.shadowBlur = 12;
            nctx.fill();

            // Connections
            for (let j = i + 1; j < nodes.length; j++) {
                const n2 = nodes[j];
                const dx = n1.x - n2.x;
                const dy = n1.y - n2.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                const maxDist = 160;

                if (dist < maxDist) {
                    const alpha = 1 - dist / maxDist;
                    nctx.beginPath();
                    nctx.moveTo(n1.x, n1.y);
                    nctx.lineTo(n2.x, n2.y);
                    nctx.lineWidth = 1;
                    nctx.strokeStyle = `rgba(0,255,255,${alpha * 0.18})`;
                    nctx.stroke();
                }
            }
        });
    }

    function drawDust() {
        if (!dctx) return;

        dctx.clearRect(0, 0, w, h);

        dusts.forEach(d => {
            d.x += d.vx;
            d.y += d.vy;

            if (d.x < 0 || d.x > w) d.vx *= -1;
            if (d.y < 0 || d.y > h) d.vy *= -1;

            dctx.beginPath();
            dctx.arc(d.x, d.y, d.s, 0, Math.PI * 2);
            dctx.fillStyle = "rgba(255,255,255,0.65)";
            dctx.shadowColor = "rgba(255,255,255,0.7)";
            dctx.shadowBlur = 8;
            dctx.fill();
        });
    }

    function animate() {
        if (nctx && dctx) {
            drawNeural();
            drawDust();
        }
        requestAnimationFrame(animate);
    }

    if (nctx && dctx) {
        animate();
    }

    // PARALLAX
    const containerOS = document.querySelector(".container-os");
    if (containerOS) {
        document.addEventListener("mousemove", e => {
            const x = (e.clientX / w - 0.5) * 20;
            const y = (e.clientY / h - 0.5) * 20;
            containerOS.style.transform = `translate(${x}px, ${y * 0.7}px)`;
        });
    }



});
