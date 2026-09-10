import React, { useEffect, useRef } from "react";
import * as THREE from "three";

interface ShelterModel3DProps {
  length: number;
  width: number;
  height: number;
  roofType: string;
  wallMaterial?: string;
  windowArea?: number;
  orientation?: string;
  className?: string;
  showLabels?: boolean;
}

export const ShelterModel3D: React.FC<ShelterModel3DProps> = ({
  length = 4.5,
  width = 3.2,
  height = 2.8,
  roofType = "pitched",
  wallMaterial = "brick",
  windowArea = 2.5,
  orientation = "south",
  className = "w-full h-full min-h-[420px]",
  showLabels = true,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const shelterGroupRef = useRef<THREE.Group | null>(null);

  // Setup Three.js scene once
  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;
    const w = container.clientWidth || 600;
    const h = container.clientHeight || 450;

    const scene = new THREE.Scene();
    sceneRef.current = scene;
    scene.background = new THREE.Color(0x0b1120); // Dark engineering navy

    const camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 100);
    camera.position.set(length * 1.8 + 2, height * 1.5 + 2, width * 1.8 + 3);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    rendererRef.current = renderer;
    container.innerHTML = "";
    container.appendChild(renderer.domElement);

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight(0xfffaed, 1.3);
    sunLight.position.set(10, 15, 8);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.width = 1024;
    sunLight.shadow.mapSize.height = 1024;
    scene.add(sunLight);

    const fillLight = new THREE.DirectionalLight(0x38bdf8, 0.4);
    fillLight.position.set(-10, 6, -8);
    scene.add(fillLight);

    // Ground plane with grid
    const grid = new THREE.GridHelper(24, 24, 0x0284c7, 0x1e293b);
    grid.position.y = -0.01;
    scene.add(grid);

    // Group for shelter geometry
    const shelterGroup = new THREE.Group();
    shelterGroupRef.current = shelterGroup;
    scene.add(shelterGroup);

    // Smooth Orbit Controls via mouse drag
    let isDragging = false;
    let prevX = 0;
    let prevY = 0;
    let theta = Math.PI / 4;
    let phi = Math.PI / 6;
    let radius = Math.max(length, width, height) * 2.8;

    const updateCamera = () => {
      phi = Math.max(0.1, Math.min(Math.PI / 2 - 0.05, phi));
      camera.position.x = radius * Math.sin(theta) * Math.cos(phi);
      camera.position.y = radius * Math.sin(phi) + height * 0.4;
      camera.position.z = radius * Math.cos(theta) * Math.cos(phi);
      camera.lookAt(0, height * 0.4, 0);
    };
    updateCamera();

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      prevX = e.clientX;
      prevY = e.clientY;
    };
    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      const dx = e.clientX - prevX;
      const dy = e.clientY - prevY;
      theta -= dx * 0.008;
      phi += dy * 0.008;
      prevX = e.clientX;
      prevY = e.clientY;
      updateCamera();
    };
    const onMouseUp = () => {
      isDragging = false;
    };
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      radius = Math.max(3, Math.min(30, radius + e.deltaY * 0.015));
      updateCamera();
    };

    container.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    container.addEventListener("wheel", onWheel, { passive: false });

    // Render loop
    let animId: number;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      if (!container) return;
      const nw = container.clientWidth;
      const nh = container.clientHeight;
      camera.aspect = nw / nh;
      camera.updateProjectionMatrix();
      renderer.setSize(nw, nh);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(animId);
      container.removeEventListener("mousedown", onMouseDown);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
      container.removeEventListener("wheel", onWheel);
      window.removeEventListener("resize", handleResize);
      renderer.dispose();
    };
  }, []);

  // Update shelter geometry whenever dimensions/materials change
  useEffect(() => {
    const group = shelterGroupRef.current;
    if (!group) return;

    // Clear previous geometry
    while (group.children.length > 0) {
      const obj = group.children[0];
      group.remove(obj);
      if (obj instanceof THREE.Mesh) {
        obj.geometry.dispose();
        if (Array.isArray(obj.material)) {
          obj.material.forEach((m) => m.dispose());
        } else {
          obj.material.dispose();
        }
      }
    }

    const L = Math.max(1.5, length);
    const W = Math.max(1.5, width);
    const H = Math.max(1.8, height);

    // Material color resolution
    let wallColor = 0xb45309; // Brick default (warm terracotta)
    let wallRoughness = 0.85;
    if (wallMaterial?.includes("wood") || wallMaterial?.includes("timber")) {
      wallColor = 0x92400e; // Wood brown
    } else if (wallMaterial?.includes("stone") || wallMaterial?.includes("granite")) {
      wallColor = 0x64748b; // Stone slate
    } else if (wallMaterial?.includes("concrete")) {
      wallColor = 0x94a3b8; // Concrete gray
    } else if (wallMaterial?.includes("puf") || wallMaterial?.includes("foam")) {
      wallColor = 0x38bdf8; // PUF cyan-tinted panel
      wallRoughness = 0.4;
    } else if (wallMaterial?.includes("mud") || wallMaterial?.includes("adobe")) {
      wallColor = 0x78350f; // Mud brick
    }

    // Foundation slab (Concrete)
    const slabGeo = new THREE.BoxGeometry(L + 0.4, 0.2, W + 0.4);
    const slabMat = new THREE.MeshStandardMaterial({
      color: 0x334155,
      roughness: 0.9,
    });
    const slabMesh = new THREE.Mesh(slabGeo, slabMat);
    slabMesh.position.y = 0.1;
    slabMesh.receiveShadow = true;
    group.add(slabMesh);

    // Wall Material
    const wallMat = new THREE.MeshStandardMaterial({
      color: wallColor,
      roughness: wallRoughness,
      metalness: 0.1,
    });

    // Main Box Shelter Walls
    const wallGeo = new THREE.BoxGeometry(L, H, W);
    const wallMesh = new THREE.Mesh(wallGeo, wallMat);
    wallMesh.position.y = 0.2 + H / 2;
    wallMesh.castShadow = true;
    wallMesh.receiveShadow = true;
    group.add(wallMesh);

    // Roof construction
    const isPitched = roofType.toLowerCase().includes("pitch");
    if (isPitched) {
      // Pitched Gabled Roof (Seamlessly matched to length and width)
      const pitchH = Math.min(1.6, W * 0.35); // 30-35 degree slope
      const roofOverhang = 0.25;

      // Triangular Prism using ExtrudeGeometry along X axis (Length)
      const triShape = new THREE.Shape();
      triShape.moveTo(-W / 2 - roofOverhang, 0);
      triShape.lineTo(0, pitchH);
      triShape.lineTo(W / 2 + roofOverhang, 0);
      triShape.closePath();

      const extrudeSettings = {
        steps: 1,
        depth: L + roofOverhang * 2,
        bevelEnabled: false,
      };

      const roofGeo = new THREE.ExtrudeGeometry(triShape, extrudeSettings);
      // Center along X and Y
      roofGeo.rotateY(Math.PI / 2);
      roofGeo.translate(0, 0.2 + H, 0);

      const roofMat = new THREE.MeshStandardMaterial({
        color: 0x1e293b, // Dark charcoal thermal roof
        roughness: 0.6,
        metalness: 0.3,
      });
      const roofMesh = new THREE.Mesh(roofGeo, roofMat);
      roofMesh.castShadow = true;
      roofMesh.receiveShadow = true;
      group.add(roofMesh);

      // Gables (Front and Back triangular infill)
      const gableGeo = new THREE.BufferGeometry();
      const vertices = new Float32Array([
        // South Gable
        -W / 2, 0.2 + H, L / 2,
        W / 2, 0.2 + H, L / 2,
        0, 0.2 + H + pitchH, L / 2,
        // North Gable
        W / 2, 0.2 + H, -L / 2,
        -W / 2, 0.2 + H, -L / 2,
        0, 0.2 + H + pitchH, -L / 2,
      ]);
      gableGeo.setAttribute("position", new THREE.BufferAttribute(vertices, 3));
      gableGeo.computeVertexNormals();
      const gableMesh = new THREE.Mesh(gableGeo, wallMat);
      gableMesh.castShadow = true;
      group.add(gableMesh);
    } else {
      // Flat Modern Insulated Roof with subtle overhang
      const flatOverhang = 0.2;
      const flatRoofGeo = new THREE.BoxGeometry(
        L + flatOverhang * 2,
        0.18,
        W + flatOverhang * 2
      );
      const flatRoofMat = new THREE.MeshStandardMaterial({
        color: 0x1e293b,
        roughness: 0.5,
        metalness: 0.4,
      });
      const flatRoofMesh = new THREE.Mesh(flatRoofGeo, flatRoofMat);
      flatRoofMesh.position.y = 0.2 + H + 0.09;
      flatRoofMesh.castShadow = true;
      flatRoofMesh.receiveShadow = true;
      group.add(flatRoofMesh);
    }

    // Windows & Glazing (South Facade, Z = +W/2)
    const winW = Math.min(L * 0.7, Math.max(1.0, Math.sqrt(windowArea * 1.2)));
    const winH = Math.min(H * 0.6, Math.max(0.8, windowArea / winW));

    // Glass panel
    const glassGeo = new THREE.PlaneGeometry(winW, winH);
    const glassMat = new THREE.MeshPhysicalMaterial({
      color: 0x38bdf8,
      transmission: 0.75,
      opacity: 0.85,
      transparent: true,
      roughness: 0.1,
      ior: 1.5,
      metalness: 0.1,
    });
    const glassMesh = new THREE.Mesh(glassGeo, glassMat);
    glassMesh.position.set(0, 0.2 + H * 0.55, W / 2 + 0.02);
    group.add(glassMesh);

    // Window Frame
    const frameGeo = new THREE.BoxGeometry(winW + 0.1, winH + 0.1, 0.06);
    const frameMat = new THREE.MeshStandardMaterial({
      color: 0x0f172a,
      roughness: 0.4,
    });
    const frameMesh = new THREE.Mesh(frameGeo, frameMat);
    frameMesh.position.set(0, 0.2 + H * 0.55, W / 2 + 0.01);
    group.add(frameMesh);

    // Front Entry Door (Wood panel, left of window)
    const doorW = 0.85;
    const doorH = 2.0;
    const doorGeo = new THREE.BoxGeometry(doorW, doorH, 0.04);
    const doorMat = new THREE.MeshStandardMaterial({
      color: 0x78350f,
      roughness: 0.7,
    });
    const doorMesh = new THREE.Mesh(doorGeo, doorMat);
    doorMesh.position.set(-L * 0.35, 0.2 + doorH / 2, W / 2 + 0.02);
    group.add(doorMesh);

    // North Arrow indicator on ground
    const arrowDir = new THREE.Vector3(0, 0, -1);
    const arrowOrigin = new THREE.Vector3(L / 2 + 1.2, 0.05, 0);
    const arrowHelper = new THREE.ArrowHelper(
      arrowDir,
      arrowOrigin,
      1.5,
      0xef4444,
      0.4,
      0.2
    );
    group.add(arrowHelper);
  }, [length, width, height, roofType, wallMaterial, windowArea, orientation]);

  return (
    <div className={`relative ${className} rounded-xl overflow-hidden eng-panel`}>
      <div ref={containerRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Floating 3D Overlays */}
      {showLabels && (
        <div className="absolute top-3 left-3 bg-slate-900/80 backdrop-blur border border-slate-700/50 rounded-lg p-2.5 text-xs text-slate-300 pointer-events-none space-y-1 z-10 shadow-lg">
          <div className="font-semibold text-sky-400 flex items-center gap-1.5">
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Digital Twin (1:1 Physics Geometry)
          </div>
          <div>
            Dimensions: <span className="text-white font-mono">{length.toFixed(1)}m × {width.toFixed(1)}m × {height.toFixed(1)}m</span>
          </div>
          <div>
            Floor Area: <span className="text-white font-mono">{(length * width).toFixed(1)} m²</span> | Vol: <span className="text-white font-mono">{(length * width * height).toFixed(1)} m³</span>
          </div>
          <div>
            Roof: <span className="text-sky-300 font-mono capitalize">{roofType}</span> | South Glazing: <span className="text-sky-300 font-mono">{windowArea.toFixed(1)} m²</span>
          </div>
        </div>
      )}

      {/* Interactive Helper Overlay */}
      <div className="absolute bottom-3 right-3 bg-slate-900/80 backdrop-blur border border-slate-700/50 rounded-lg px-2.5 py-1 text-[11px] text-slate-400 pointer-events-none z-10">
        🖱️ Drag to Orbit · Scroll to Zoom
      </div>

      {/* North Compass Badge */}
      <div className="absolute top-3 right-3 bg-slate-900/80 backdrop-blur border border-rose-500/30 rounded-lg px-2.5 py-1 text-[11px] font-semibold text-rose-400 pointer-events-none z-10 flex items-center gap-1">
        <span>↑</span>
        <span>NORTH</span>
      </div>
    </div>
  );
};
