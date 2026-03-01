/**
 * Ported Legacy Mindmap Component (v4.0)
 * Handles radial tree layout, bezier edges, and interactive node physics on Canvas.
 */

class SoulMindmap {
    constructor(canvasId, tooltipId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');
        this.tooltip = document.getElementById(tooltipId);

        this.nodes = [];
        this.edges = [];
        this.nodeAnim = {};
        this.particles = [];
        this.cam = { x: 0, y: 0, zoom: 1, targetX: 0, targetY: 0, targetZoom: 1 };
        this.hoveredNode = null;
        this.isDragging = false;
        this.animTime = 0;

        this.SECTION_COLORS = {
            'Personality': '#f0a050',
            'Philosophy': '#7e74f1',
            'Boundaries': '#e05050',
            'Continuity': '#50b8e0',
        };

        this.init();
    }

    init() {
        window.addEventListener('resize', () => this.resize());
        this.resize();
        this.setupListeners();
        this.animate();
    }

    resize() {
        const rect = this.canvas.parentElement.getBoundingClientRect();
        this.canvas.width = rect.width * window.devicePixelRatio;
        this.canvas.height = rect.height * window.devicePixelRatio;
        this.ctx.setTransform(window.devicePixelRatio, 0, 0, window.devicePixelRatio, 0, 0);
        this.W = rect.width;
        this.H = rect.height;
    }

    setData(data) {
        const { nodes, edges } = this.buildNodes(data);
        this.nodes = nodes;
        this.edges = edges;
        this.layoutRadial();

        this.nodes.forEach(n => {
            this.nodeAnim[n.id] = { scale: 0, targetScale: 1, visible: true };
        });

        // Quick grow stagger
        this.nodes.forEach((n, i) => {
            setTimeout(() => { if (this.nodeAnim[n.id]) this.nodeAnim[n.id].targetScale = 1; }, i * 20);
        });

        this.fitToVisible(true);
    }

    buildNodes(data) {
        const nodes = [];
        const edges = [];
        let nid = 0;

        const root = { id: nid++, type: 'root', label: 'SOUL', x: 0, y: 0, r: 24, color: '#7e74f1', depth: 0 };
        nodes.push(root);

        (data.soul_tree || []).forEach(sec => {
            const color = this.getSecColor(sec.text);
            const sNode = { id: nid++, type: 'section', label: sec.text, x: 0, y: 0, r: 20, color, depth: 1, parentId: root.id };
            nodes.push(sNode);
            edges.push({ from: root.id, to: sNode.id, color });

            (sec.children || []).forEach(child => {
                if (child.type === 'subsection') {
                    const subNode = { id: nid++, type: 'subsection', label: child.text, x: 0, y: 0, r: 16, color, depth: 2, parentId: sNode.id };
                    nodes.push(subNode);
                    edges.push({ from: sNode.id, to: subNode.id, color });

                    (child.children || []).forEach(b => {
                        const bNode = {
                            id: nid++, type: 'bullet', label: b.text, tag: b.tag,
                            x: 0, y: 0, r: 12,
                            color: b.tag === 'CORE' ? '#e05050' : (b.tag === 'MUTABLE' ? '#50c878' : '#666'),
                            depth: 3, parentId: subNode.id,
                            label: b.text.length > 50 ? b.text.slice(0, 47) + '...' : b.text
                        };
                        nodes.push(bNode);
                        edges.push({ from: subNode.id, to: bNode.id, color: bNode.color });
                    });
                }
            });
        });

        return { nodes, edges };
    }

    getSecColor(name) {
        for (const [k, v] of Object.entries(this.SECTION_COLORS)) {
            if (name.includes(k)) return v;
        }
        return '#888';
    }

    layoutRadial() {
        const childrenOf = {};
        this.edges.forEach(e => {
            if (!childrenOf[e.from]) childrenOf[e.from] = [];
            childrenOf[e.from].push(e.to);
        });

        const nodeMap = {};
        this.nodes.forEach(n => nodeMap[n.id] = n);

        const countLeaves = (nid) => {
            const kids = childrenOf[nid] || [];
            if (kids.length === 0) return 1;
            return kids.reduce((s, k) => s + countLeaves(k), 0);
        }

        const layout = (nid, angleStart, angleEnd, radius) => {
            const node = nodeMap[nid];
            const kids = childrenOf[nid] || [];
            const mid = (angleStart + angleEnd) / 2;

            if (nid !== 0) {
                node.x = Math.cos(mid) * radius;
                node.y = Math.sin(mid) * radius;
            }

            if (kids.length === 0) return;

            const totalLeaves = countLeaves(nid);
            let cursor = angleStart;

            kids.forEach(kid => {
                const kidNode = nodeMap[kid];
                const leaves = countLeaves(kid);
                const share = (leaves / totalLeaves) * (angleEnd - angleStart);
                layout(kid, cursor, cursor + share, radius + this.radiusStep(kidNode.depth));
                cursor += share;
            });
        }

        layout(0, -Math.PI, Math.PI, 0);
    }

    radiusStep(depth) {
        if (depth === 1) return 140;
        if (depth === 2) return 110;
        return 90;
    }

    setupListeners() {
        this.canvas.addEventListener('mousedown', e => {
            this.isDragging = true;
            this.dragStartX = e.clientX; this.dragStartY = e.clientY;
            this.camStartX = this.cam.x; this.camStartY = this.cam.y;
        });
        window.addEventListener('mousemove', e => this.handleMouseMove(e));
        window.addEventListener('mouseup', () => { this.isDragging = false; });
        this.canvas.addEventListener('wheel', e => this.handleWheel(e), { passive: false });
    }

    handleMouseMove(e) {
        if (this.isDragging) {
            this.cam.x = this.cam.targetX = this.camStartX - (e.clientX - this.dragStartX) / this.cam.zoom;
            this.cam.y = this.cam.targetY = this.camStartY - (e.clientY - this.dragStartY) / this.cam.zoom;
        }

        const rect = this.canvas.getBoundingClientRect();
        const wx = (e.clientX - rect.left - this.W / 2) / this.cam.zoom + this.cam.x;
        const wy = (e.clientY - rect.top - this.H / 2) / this.cam.zoom + this.cam.y;

        let found = null;
        for (let i = this.nodes.length - 1; i >= 0; i--) {
            const n = this.nodes[i];
            const dx = wx - n.x; const dy = wy - n.y;
            if (dx * dx + dy * dy < (n.r + 5) * (n.r + 5)) { found = n; break; }
        }

        this.hoveredNode = found;
        if (found && this.tooltip) {
            this.tooltip.style.opacity = 1;
            this.tooltip.style.left = (e.clientX + 15) + 'px';
            this.tooltip.style.top = (e.clientY + 15) + 'px';
            this.tooltip.textContent = found.label;
        } else if (this.tooltip) {
            this.tooltip.style.opacity = 0;
        }
    }

    handleWheel(e) {
        e.preventDefault();
        const factor = e.deltaY > 0 ? 0.9 : 1.1;
        this.cam.targetZoom = Math.max(0.2, Math.min(5, this.cam.targetZoom * factor));
    }

    fitToVisible(instant) {
        let maxDist = 80;
        this.nodes.forEach(n => {
            const dist = Math.sqrt(n.x * n.x + n.y * n.y) + n.r + 40;
            if (dist > maxDist) maxDist = dist;
        });
        const zoom = Math.min(this.W / (maxDist * 2.2), this.H / (maxDist * 2.2), 2);
        this.cam.targetX = 0; this.cam.targetY = 0; this.cam.targetZoom = zoom;
        if (instant) {
            this.cam.x = 0; this.cam.y = 0; this.cam.zoom = zoom;
            this.cam.targetZoom = zoom;
        }
    }

    animate() {
        this.animTime += 0.016;
        this.cam.x += (this.cam.targetX - this.cam.x) * 0.1;
        this.cam.y += (this.cam.targetY - this.cam.y) * 0.1;
        this.cam.zoom += (this.cam.targetZoom - this.cam.zoom) * 0.1;

        this.nodes.forEach(n => {
            const a = this.nodeAnim[n.id];
            if (a) a.scale += (a.targetScale - a.scale) * 0.1;
        });

        this.draw();
        requestAnimationFrame(() => this.animate());
    }

    draw() {
        this.ctx.clearRect(0, 0, this.W, this.H);
        this.ctx.save();
        this.ctx.translate(this.W / 2, this.H / 2);
        this.ctx.scale(this.cam.zoom, this.cam.zoom);
        this.ctx.translate(-this.cam.x, -this.cam.y);

        // Edges
        this.edges.forEach(e => {
            const from = this.nodes.find(n => n.id === e.from);
            const to = this.nodes.find(n => n.id === e.to);
            const s = Math.min(this.nodeAnim[from.id].scale, this.nodeAnim[to.id].scale);
            if (s < 0.01) return;

            this.ctx.beginPath();
            this.ctx.moveTo(from.x, from.y);
            this.ctx.lineTo(to.x, to.y);
            this.ctx.strokeStyle = e.color + '44'; // transparency
            this.ctx.lineWidth = 2.5;
            this.ctx.stroke();
        });

        // Nodes
        this.nodes.forEach(n => {
            const s = this.nodeAnim[n.id].scale;
            if (s < 0.01) return;

            const isHov = this.hoveredNode && this.hoveredNode.id === n.id;
            const r = n.r * s * (isHov ? 1.2 : 1);

            this.ctx.beginPath();
            this.ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
            this.ctx.fillStyle = n.color;
            this.ctx.shadowBlur = isHov ? 15 : 5;
            this.ctx.shadowColor = n.color;
            this.ctx.fill();
            this.ctx.shadowBlur = 0;

            if (n.type === 'root' || n.type === 'section') {
                this.ctx.font = `bold ${8 + r / 2}px JetBrains Mono`;
                this.ctx.fillStyle = '#fff';
                this.ctx.textAlign = 'center';
                this.ctx.fillText(n.label, n.x, n.y + 4);
            }
        });

        this.ctx.restore();
    }
}

window.SoulMindmap = SoulMindmap;
