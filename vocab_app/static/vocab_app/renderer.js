import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';

export class GalaxyRenderer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.labelRenderer = null;
        this.controls = null;
        this.labels = [];
        this.wordsData = [];
        this.scaleFactor = 400;

        // Initial "north" orientation
        this.initialCameraPos = new THREE.Vector3(0, 200, 900);
        this.initialTarget = new THREE.Vector3(0, 0, 0);
        this._resetting = false;
        this._resetAlpha = 0;

        this.onWordClick = null; // Callback for when a word is clicked

        this.init();
        this.animate();
    }

    init() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x050510);
        this.scene.fog = new THREE.FogExp2(0x050510, 0.0015);

        this.camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 1, 5000);
        this.camera.position.set(0, 200, 900);

        // Stars
        const geometry = new THREE.BufferGeometry();
        const vertices = [];
        for (let i = 0; i < 3000; i++) {
            vertices.push(THREE.MathUtils.randFloatSpread(4000));
            vertices.push(THREE.MathUtils.randFloatSpread(4000));
            vertices.push(THREE.MathUtils.randFloatSpread(4000));
        }
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
        const particles = new THREE.Points(geometry, new THREE.PointsMaterial({ color: 0x888888, size: 2 }));
        this.scene.add(particles);

        // Reference Sphere
        const sphereGeo = new THREE.SphereGeometry(this.scaleFactor, 32, 32);
        const sphereMat = new THREE.MeshBasicMaterial({ color: 0x4444ff, wireframe: true, transparent: true, opacity: 0.03 });
        this.scene.add(new THREE.Mesh(sphereGeo, sphereMat));

        // Renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.container.appendChild(this.renderer.domElement);

        // Label Renderer
        this.labelRenderer = new CSS2DRenderer();
        this.labelRenderer.setSize(window.innerWidth, window.innerHeight);
        this.labelRenderer.domElement.style.position = 'absolute';
        this.labelRenderer.domElement.style.top = '0px';
        this.labelRenderer.domElement.style.pointerEvents = 'none'; // Pass events through to labels/controls
        this.labelRenderer.domElement.style.zIndex = '1';
        this.container.appendChild(this.labelRenderer.domElement);

        this.renderer.domElement.style.position = 'absolute';
        this.renderer.domElement.style.top = '0px';
        this.renderer.domElement.style.zIndex = '0';
        this.renderer.domElement.style.pointerEvents = 'auto';

        // Controls - Attach to renderer.domElement (the canvas)
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.minDistance = 100;
        this.controls.maxDistance = 2000;
        this.controls.autoRotate = true;
        this.controls.autoRotateSpeed = 0.5;

        window.addEventListener('resize', () => this.onWindowResize());
    }

    onWindowResize() {
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.labelRenderer.setSize(window.innerWidth, window.innerHeight);
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        // Smooth reset animation
        if (this._resetting) {
            this._resetAlpha += 0.03;
            const t = Math.min(this._resetAlpha, 1);
            const ease = t * (2 - t); // ease-out quad
            this.camera.position.lerpVectors(this._resetFrom, this.initialCameraPos, ease);
            this.controls.target.lerpVectors(this._resetTargetFrom, this.initialTarget, ease);
            if (t >= 1) {
                this._resetting = false;
                this.controls.autoRotate = true;
            }
        }

        this.controls.update();

        // Distance-based opacity
        const sphereRadius = this.scaleFactor;
        const camDist = this.camera.position.length();
        const minDist = Math.max(0, camDist - sphereRadius);
        const maxDist = camDist + sphereRadius;
        const range = maxDist - minDist;

        this.labels.forEach(label => {
            const dist = label.position.distanceTo(this.camera.position);
            let normDist = (dist - minDist) / (range || 1);
            let opacity = 1.0 - Math.pow(normDist, 1.5);
            opacity = Math.max(0.1, Math.min(1.0, opacity));
            label.element.style.opacity = opacity;
        });

        this.renderer.render(this.scene, this.camera);
        this.labelRenderer.render(this.scene, this.camera);
    }

    resetView() {
        this._resetFrom = this.camera.position.clone();
        this._resetTargetFrom = this.controls.target.clone();
        this._resetAlpha = 0;
        this._resetting = true;
        this.controls.autoRotate = false; // pause during animation
    }

    updateData(wordsData, filters = { cluster: 'all', type: 'all', addDate: 'all', reviewDate: 'all', srsLevel: 'all', component: null, search: '' }) {
        console.log("Updating Galaxy with words:", wordsData.length);
        this.wordsData = wordsData;

        // Remove existing labels
        this.labels.forEach(l => this.scene.remove(l));
        this.labels = [];

        const palette = {
            // --- Original Colors ---
            1: '#FF5733', // Vibrant Orange-Red
            2: '#33FF57', // Neon Lime Green
            3: '#3357FF', // Bright Blue
            4: '#F333FF', // Magenta / Hot Pink
            5: '#FFFF33', // Bright Yellow
            6: '#33FFFF', // Cyan / Aqua
            7: '#FF3385', // Pink
            8: '#95A5A6', // Concrete (Medium Gray)
            9: '#FF8C00', // Dark Orange
            10: '#2ECC71', // Emerald Green
            11: '#C0392B', // Strong Red
        };

        const now = new Date();
        const oneDay = 24 * 60 * 60 * 1000;

        const checkDate = (dateStr, filter) => {
            if (filter === 'all') return true;
            if (filter === 'never') return !dateStr;
            if (!dateStr) return false;

            const date = new Date(dateStr);
            const diffTime = Math.abs(now - date);
            const diffDays = Math.ceil(diffTime / oneDay);

            if (filter === 'today') return diffDays <= 1;
            if (filter === 'week') return diffDays <= 7;
            if (filter === 'month') return diffDays <= 30;
            return true;
        };

        wordsData.forEach(item => {
            // Apply filtering
            if (filters.cluster !== 'all' && item.cluster_id != filters.cluster) return;
            if (filters.type !== 'all' && (item.flashcard_infos?.word_type != filters.type)) return;

            // Add Date Filter
            if (!checkDate(item.add_date, filters.addDate)) return;

            // Review Date Filter
            if (!checkDate(item.last_review_date, filters.reviewDate)) return;

            // SRS Level Filter
            if (filters.srsLevel !== 'all') {
                const level = item.srs_level || 0;
                if (filters.srsLevel === '0' && level !== 0) return;
                if (filters.srsLevel === '1-3' && (level < 1 || level > 3)) return;
                if (filters.srsLevel === '4-6' && (level < 4 || level > 6)) return;
                if (filters.srsLevel === '7+' && level < 7) return;
            }

            // Component filter: show word if its Thai text IS the component, or if its components list includes it
            if (filters.component) {
                const comp = filters.component;
                const parts = item.flashcard_infos?.components?.[0] || [];
                const isMatch = item.word.thai === comp || parts.includes(comp);
                if (!isMatch) return;
            }

            // Search filter
            if (filters.search) {
                const q = filters.search;
                const thai = (item.word.thai || '').toLowerCase();
                const french = (item.word.french || '').toLowerCase();
                const rom = (item.flashcard_infos?.romanization || '').toLowerCase();

                if (!thai.includes(q) && !french.includes(q) && !rom.includes(q)) {
                    return;
                }
            }

            const div = document.createElement('div');
            div.className = 'label';
            const color = palette[item.cluster_id] || '#ffffff';
            div.style.color = color;
            div.style.boxShadow = `0 0 10px ${color}44`;
            div.textContent = item.word.thai;
            div.style.pointerEvents = 'auto';

            div.onclick = (e) => {
                console.log("Word clicked:", item.word.thai);
                e.stopPropagation();
                if (this.onWordClick) this.onWordClick(item);
            };

            const label = new CSS2DObject(div);
            // Coordinates from API are normalized (-1 to 1), scale to galaxy size
            const x = (item.x || 0) * this.scaleFactor;
            const y = (item.y || 0) * this.scaleFactor;
            const z = (item.z || 0) * this.scaleFactor;
            label.position.set(x, y, z);

            this.scene.add(label);
            this.labels.push(label);
        });

        if (this.labels.length === 0 && wordsData.length > 0) {
            console.warn("All words filtered out or missing coordinates");
        }
    }
}
