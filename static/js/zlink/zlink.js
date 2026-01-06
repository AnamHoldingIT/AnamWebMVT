document.addEventListener("DOMContentLoaded", () => {

    /* ============================================================
       1) OPTIMIZED BACKGROUND — NEURAL NETWORK + QUANTUM DUST
       ============================================================ */

    const neuralCanvas = document.getElementById("neural-layer");
    const dustCanvas = document.getElementById("quantum-dust");
    const containerOS = document.querySelector(".container-os");

    let nctx = null;
    let dctx = null;

    if (neuralCanvas && dustCanvas) {
        nctx = neuralCanvas.getContext("2d", {alpha: true});
        dctx = dustCanvas.getContext("2d", {alpha: true});
    }

    let w = window.innerWidth;
    let h = window.innerHeight;

    // متغیرهای ماوس و پارالکس
    const mouse = {x: -9999, y: -9999};
    const parallax = {targetX: 0, targetY: 0, currentX: 0, currentY: 0};

    function resize() {
        w = window.innerWidth;
        h = window.innerHeight;

        if (neuralCanvas && dustCanvas) {
            neuralCanvas.width = dustCanvas.width = w;
            neuralCanvas.height = dustCanvas.height = h;
        }
    }

    window.addEventListener("resize", resize);
    resize();

    const isMobile = w < 768;
    const NODE_COUNT = isMobile ? 50 : 80;
    const DUST_COUNT = isMobile ? 30 : 60;

    let nodes = [];
    let dusts = [];

    function initNodes() {
        nodes = [];
        for (let i = 0; i < NODE_COUNT; i++) {
            nodes.push({
                x: Math.random() * w,
                y: Math.random() * h,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                s: Math.random() * 2 + 1.2
            });
        }
    }

    function initDust() {
        dusts = [];
        for (let i = 0; i < DUST_COUNT; i++) {
            dusts.push({
                x: Math.random() * w,
                y: Math.random() * h,
                vx: (Math.random() - 0.5) * 0.2,
                vy: (Math.random() - 0.5) * 0.2,
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

        parallax.targetX = (e.clientX / w - 0.5) * 20;
        parallax.targetY = (e.clientY / h - 0.5) * 20;
    });

    window.addEventListener("mouseleave", () => {
        mouse.x = -9999;
        mouse.y = -9999;
        parallax.targetX = 0;
        parallax.targetY = 0;
    });

    const maxConnectionDist = 160;
    const maxConnectionDistSq = maxConnectionDist * maxConnectionDist;
    const influenceRadius = 140;
    const influenceRadiusSq = influenceRadius * influenceRadius;

    function drawSystem() {
        nctx.clearRect(0, 0, w, h);
        dctx.clearRect(0, 0, w, h);

        if (containerOS) {
            parallax.currentX += (parallax.targetX - parallax.currentX) * 0.08;
            parallax.currentY += (parallax.targetY - parallax.currentY) * 0.08;
            containerOS.style.transform = `translate3d(${parallax.currentX}px, ${parallax.currentY * 0.7}px, 0)`;
        }

        const len = nodes.length;

        for (let i = 0; i < len; i++) {
            let n1 = nodes[i];

            n1.x += n1.vx;
            n1.y += n1.vy;

            if (n1.x < 0 || n1.x > w) n1.vx *= -1;
            if (n1.y < 0 || n1.y > h) n1.vy *= -1;

            const dxM = n1.x - mouse.x;
            const dyM = n1.y - mouse.y;
            const distMSq = dxM * dxM + dyM * dyM;

            if (distMSq < influenceRadiusSq) {
                const distM = Math.sqrt(distMSq);
                const force = (influenceRadius - distM) / influenceRadius * 0.25;
                n1.x += dxM * force;
                n1.y += dyM * force;
            }

            nctx.beginPath();
            nctx.arc(n1.x, n1.y, n1.s, 0, Math.PI * 2);
            nctx.fillStyle = "rgba(0,255,255,0.9)";
            nctx.fill();

            for (let j = i + 1; j < len; j++) {
                const n2 = nodes[j];
                const dx = n1.x - n2.x;
                const dy = n1.y - n2.y;
                const distSq = dx * dx + dy * dy;

                if (distSq < maxConnectionDistSq) {
                    const dist = Math.sqrt(distSq);
                    const alpha = 1 - dist / maxConnectionDist;

                    nctx.beginPath();
                    nctx.moveTo(n1.x, n1.y);
                    nctx.lineTo(n2.x, n2.y);
                    nctx.lineWidth = 1;
                    nctx.strokeStyle = `rgba(0,255,255,${alpha * 0.18})`;
                    nctx.stroke();
                }
            }
        }

        dusts.forEach(d => {
            d.x += d.vx;
            d.y += d.vy;

            if (d.x < 0 || d.x > w) d.vx *= -1;
            if (d.y < 0 || d.y > h) d.vy *= -1;

            dctx.beginPath();
            dctx.arc(d.x, d.y, d.s, 0, Math.PI * 2);
            dctx.fillStyle = "rgba(255,255,255,0.65)";
            dctx.fill();
        });

        requestAnimationFrame(drawSystem);
    }

    if (nctx && dctx) {
        drawSystem();
    }
});