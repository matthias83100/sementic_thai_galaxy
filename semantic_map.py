import numpy as np
import json

print("Applying 'Security Spacing' algorithm...")

# 1. Get Base Coordinates (Unit Sphere)
# We verify we have the centered sphere coordinates
coords = df[['x', 'y', 'z']].values
centered_coords = coords - np.mean(coords, axis=0)
norms = np.linalg.norm(centered_coords, axis=1, keepdims=True)
initial_embeddings = centered_coords / norms

# 2. Define Repulsion Function
def apply_repulsion(coords, min_dist=0.12, iterations=100):
    """
    Iteratively pushes points apart if they are closer than min_dist.
    Constraints points to the unit sphere surface.
    """
    new_coords = coords.copy()
    count = 0
    
    for it in range(iterations):
        moved = False
        # Simple pairwise repulsion
        for i in range(len(new_coords)):
            for j in range(i + 1, len(new_coords)):
                p1 = new_coords[i]
                p2 = new_coords[j]
                
                diff = p1 - p2
                dist = np.linalg.norm(diff)
                
                # If too close (and not the same point)
                if dist < min_dist and dist > 1e-6:
                    # Calculate repulsion vector
                    # Move each point away by half the overlap
                    correction = (diff / dist) * (min_dist - dist) * 0.5
                    new_coords[i] += correction
                    new_coords[j] -= correction
                    moved = True
        
        # Important: Project back to sphere surface
        norms = np.linalg.norm(new_coords, axis=1, keepdims=True)
        new_coords = new_coords / norms
        
        if not moved:
            break
        count = it
        
    print(f"Spacing optimization finished in {count} iterations.")
    return new_coords

# 3. Run Optimization
# min_dist=0.15 is about 7.5% of the diameter, good for readability
spaced_embeddings = apply_repulsion(initial_embeddings, min_dist=0.15)

# 4. Generate HTML (Same logic as before, but with spaced coords)
x_spread, y_spread, z_spread = spaced_embeddings.T
scale_factor = 400 

chart_data = []

# Palette for clusters
palette = {
    1: '#FF5733', 2: '#33FF57', 3: '#3357FF', 4: '#F333FF', 
    5: '#FFFF33', 6: '#33FFFF', 7: '#FF3385'
}

for i in range(len(df)):
    color = "#ffffff"
    if 'cluster_id' in df.columns:
        cid = df.iloc[i]['cluster_id']
        color = palette.get(cid, "#ffffff")
    
    chart_data.append({
        "thai": df.iloc[i]['thai'],
        "french": df.iloc[i]['french'],
        "x": float(x_spread[i]) * scale_factor,
        "y": float(y_spread[i]) * scale_factor,
        "z": float(z_spread[i]) * scale_factor,
        "color": color
    })

json_data = json.dumps(chart_data)

# HTML Template (Identical to previous, ensuring we keep the style)
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Thai Semantic Galaxy (Spaced)</title>
    <style>
        body {{ margin: 0; background-color: #000; overflow: hidden; font-family: 'Sarabun', 'Garuda', sans-serif; }}
        #container {{ width: 100vw; height: 100vh; }}
        .label {{ 
            color: white; font-size: 14px; font-weight: bold; 
            text-shadow: 0 0 5px #000, 0 0 10px currentColor; 
            cursor: pointer; user-select: none; transition: opacity 0.1s ease;
            white-space: nowrap; padding: 2px 5px; border-radius: 4px; background: rgba(0,0,0,0.2);
        }}
        .label:hover {{ z-index: 1000 !important; font-size: 18px; background: rgba(0,0,0,0.8); border: 1px solid white; }}
        .french-trans {{ display: block; font-size: 0.8em; color: #ddd; font-weight: normal; margin-top: 2px; }}
    </style>
    <script type="importmap">
      {{ "imports": {{ "three": "https://unpkg.com/three@0.160.0/build/three.module.js", "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/" }} }}
    </script>
</head>
<body>
    <div id="container"></div>
    <script type="module">
        import * as THREE from 'three';
        import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
        import {{ CSS2DRenderer, CSS2DObject }} from 'three/addons/renderers/CSS2DRenderer.js';

        const data = {json_data};
        let camera, scene, renderer, labelRenderer, controls, labels = [];

        init();
        animate();

        function init() {{
            const container = document.getElementById('container');
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x050510);
            scene.fog = new THREE.FogExp2(0x050510, 0.0015);

            camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 1, 5000);
            camera.position.set(0, 200, 900);

            // Stars
            const geometry = new THREE.BufferGeometry();
            const vertices = [];
            for ( let i = 0; i < 2000; i ++ ) {{
                vertices.push( THREE.MathUtils.randFloatSpread( 3000 ) );
                vertices.push( THREE.MathUtils.randFloatSpread( 3000 ) );
                vertices.push( THREE.MathUtils.randFloatSpread( 3000 ) );
            }}
            geometry.setAttribute( 'position', new THREE.Float32BufferAttribute( vertices, 3 ) );
            const particles = new THREE.Points( geometry, new THREE.PointsMaterial( {{ color: 0x888888, size: 2 }} ) );
            scene.add( particles );

            // Reference Sphere
            const sphereGeo = new THREE.SphereGeometry({scale_factor}, 32, 32);
            const sphereMat = new THREE.MeshBasicMaterial({{ color: 0x4444ff, wireframe: true, transparent: true, opacity: 0.05 }});
            scene.add(new THREE.Mesh(sphereGeo, sphereMat));

            // Words
            const labelContainer = new THREE.Group();
            scene.add(labelContainer);
            data.forEach(item => {{
                const div = document.createElement('div');
                div.className = 'label';
                div.style.color = item.color;
                div.innerHTML = `${{item.thai}}<span class="french-trans" style="display:none">${{item.french}}</span>`;
                div.onmouseenter = () => div.querySelector('.french-trans').style.display = 'block';
                div.onmouseleave = () => div.querySelector('.french-trans').style.display = 'none';
                const label = new CSS2DObject(div);
                label.position.set(item.x, item.y, item.z);
                labelContainer.add(label);
                labels.push(label);
            }});

            renderer = new THREE.WebGLRenderer({{ antialias: true }} );
            renderer.setPixelRatio( window.devicePixelRatio );
            renderer.setSize( window.innerWidth, window.innerHeight );
            container.appendChild( renderer.domElement );

            labelRenderer = new CSS2DRenderer();
            labelRenderer.setSize( window.innerWidth, window.innerHeight );
            labelRenderer.domElement.style.position = 'absolute';
            labelRenderer.domElement.style.top = '0px';
            container.appendChild( labelRenderer.domElement );

            controls = new OrbitControls( camera, labelRenderer.domElement );
            controls.enableDamping = true; controls.dampingFactor = 0.05;
            controls.minDistance = 100; controls.maxDistance = 2000;
            controls.autoRotate = true; controls.autoRotateSpeed = 0.5;
            window.addEventListener( 'resize', onWindowResize );
        }}

        function onWindowResize() {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize( window.innerWidth, window.innerHeight );
            labelRenderer.setSize( window.innerWidth, window.innerHeight );
        }}

        function animate() {{
            requestAnimationFrame( animate );
            controls.update();
            
            // Visibility Logic
            const sphereRadius = {scale_factor};
            const camDist = camera.position.length();
            const minDist = Math.max(0, camDist - sphereRadius);
            const maxDist = camDist + sphereRadius;
            const range = maxDist - minDist;

            labels.forEach(label => {{
                const dist = label.position.distanceTo(camera.position);
                let normDist = (dist - minDist) / (range || 1);
                let opacity = 1.0 - Math.pow(normDist, 1.5);
                opacity = Math.max(0.15, Math.min(1.0, opacity));
                label.element.style.opacity = opacity;
            }});

            renderer.render( scene, camera );
            labelRenderer.render( scene, camera );
        }}
    </script>
</body>
</html>
"""
