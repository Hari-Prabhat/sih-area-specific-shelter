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

  // Setup Three.js scene once.
  useEffect(() => {
    if (!containerRef.current) return;

    const container = containerRef.current;
    const w = Math.max(container.clientWidth, 1);
    const h = Math.max(container.clientHeight, 1);

    const scene = new THREE.Scene();
    sceneRef.current = scene;
    scene.background = new THREE.Color(0x0b1120);

    const camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 100);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
    });
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    rendererRef.current = renderer;

    container.innerHTML = "";
    container.appendChild(renderer.domElement);

    // Lighting.
    scene.add(new THREE.AmbientLight(0xffffff, 0.72));

    const sunLight = new THREE.DirectionalLight(0xfffaed, 1.25);
    sunLight.position.set(10, 15, 8);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.set(1024, 1024);
    scene.add(sunLight);

    const fillLight = new THREE.DirectionalLight(0x38bdf8, 0.35);
    fillLight.position.set(-10, 6, -8);
    scene.add(fillLight);

    // Ground.
    const grid = new THREE.GridHelper(24, 24, 0x0284c7, 0x1e293b);
    grid.position.y = -0.01;
    scene.add(grid);

    const shelterGroup = new THREE.Group();
    shelterGroupRef.current = shelterGroup;
    scene.add(shelterGroup);

    // Camera orbit state.
    let isDragging = false;
    let prevX = 0;
    let prevY = 0;
    let theta = Math.PI / 4;
    let phi = Math.PI / 6;
    let radius = 10;

    const updateCamera = () => {
      phi = Math.max(0.12, Math.min(Math.PI / 2 - 0.05, phi));
      radius = Math.max(4, Math.min(30, radius));

      camera.position.set(
        radius * Math.sin(theta) * Math.cos(phi),
        radius * Math.sin(phi) + 1.2,
        radius * Math.cos(theta) * Math.cos(phi)
      );
      camera.lookAt(0, 1.4, 0);
    };

    updateCamera();

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      prevX = e.clientX;
      prevY = e.clientY;
      renderer.domElement.style.cursor = "grabbing";
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
      renderer.domElement.style.cursor = "grab";
    };

    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      radius += e.deltaY * 0.015;
      updateCamera();
    };

    container.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    container.addEventListener("wheel", onWheel, { passive: false });

    let animId = 0;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      const nw = Math.max(container.clientWidth, 1);
      const nh = Math.max(container.clientHeight, 1);

      camera.aspect = nw / nh;
      camera.updateProjectionMatrix();
      renderer.setSize(nw, nh);
    };

    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(container);

    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(animId);
      resizeObserver.disconnect();

      container.removeEventListener("mousedown", onMouseDown);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
      container.removeEventListener("wheel", onWheel);
      window.removeEventListener("resize", handleResize);

      renderer.dispose();
      renderer.domElement.remove();
      scene.clear();

      sceneRef.current = null;
      rendererRef.current = null;
      cameraRef.current = null;
      shelterGroupRef.current = null;
    };
  }, []);

  // Rebuild the parametric shelter whenever an engineering input changes.
  useEffect(() => {
    const group = shelterGroupRef.current;
    if (!group) return;

    while (group.children.length > 0) {
      const obj = group.children[0];
      group.remove(obj);

      obj.traverse((child) => {
        if (child instanceof THREE.Mesh) {
          child.geometry.dispose();

          if (Array.isArray(child.material)) {
            child.material.forEach((material) => material.dispose());
          } else {
            child.material.dispose();
          }
        }
      });
    }

    const L = Math.max(2.0, Number(length) || 4.5);
    const W = Math.max(1.5, Number(width) || 3.2);
    const H = Math.max(2.0, Number(height) || 2.8);
    const glazingArea = Math.max(0.2, Number(windowArea) || 2.5);

    // Wall appearance.
    let wallColor = 0xb45309;
    let wallRoughness = 0.85;

    const materialName = (wallMaterial || "").toLowerCase();

    if (
      materialName.includes("wood") ||
      materialName.includes("timber")
    ) {
      wallColor = 0x92400e;
    } else if (
      materialName.includes("stone") ||
      materialName.includes("granite")
    ) {
      wallColor = 0x64748b;
    } else if (materialName.includes("concrete")) {
      wallColor = 0x94a3b8;
    } else if (
      materialName.includes("puf") ||
      materialName.includes("foam")
    ) {
      wallColor = 0x38bdf8;
      wallRoughness = 0.4;
    } else if (
      materialName.includes("mud") ||
      materialName.includes("adobe")
    ) {
      wallColor = 0x78350f;
    }

    const wallMat = new THREE.MeshStandardMaterial({
      color: wallColor,
      roughness: wallRoughness,
      metalness: 0.05,
    });

    // Raised foundation/plinth.
    const slabHeight = 0.2;
    const slabOverhang = 0.2;

    const slab = new THREE.Mesh(
      new THREE.BoxGeometry(L + slabOverhang * 2, slabHeight, W + slabOverhang * 2),
      new THREE.MeshStandardMaterial({
        color: 0x334155,
        roughness: 0.9,
      })
    );

    slab.position.y = slabHeight / 2;
    slab.castShadow = true;
    slab.receiveShadow = true;
    group.add(slab);

    // Main rectangular wall volume.
    const walls = new THREE.Mesh(
      new THREE.BoxGeometry(L, H, W),
      wallMat
    );

    walls.position.y = slabHeight + H / 2;
    walls.castShadow = true;
    walls.receiveShadow = true;
    group.add(walls);

    const wallTop = slabHeight + H;
    const isPitched = (roofType || "").toLowerCase().includes("pitch");

    if (isPitched) {
      /*
       * Correct gable roof:
       *
       *                 ridge
       *                  /\
       *                 /  \
       *                /    \
       *       eave ___/      \___ eave
       *
       * The roof is built from two rectangular panels. This avoids the
       * previous ExtrudeGeometry translation error that shifted the roof
       * along the X axis.
       */
      const roofOverhang = 0.25;
      const roofThickness = 0.14;

      const halfRoofSpan = W / 2 + roofOverhang;

      // Keep the roof slope realistic and tied to shelter width.
      const pitchHeight = Math.min(1.6, Math.max(0.65, W * 0.35));
      const roofAngle = Math.atan2(pitchHeight, halfRoofSpan);
      const roofPanelLength = Math.sqrt(
        halfRoofSpan * halfRoofSpan + pitchHeight * pitchHeight
      );

      const roofMat = new THREE.MeshStandardMaterial({
        color: 0x1e293b,
        roughness: 0.62,
        metalness: 0.18,
      });

      // Extend roof beyond both end walls in the X direction.
      const roofLength = L + roofOverhang * 2;

      // Positive-Z roof slope.
      const roofSouth = new THREE.Mesh(
        new THREE.BoxGeometry(
          roofLength,
          roofThickness,
          roofPanelLength
        ),
        roofMat
      );

      roofSouth.position.set(
        0,
        wallTop + pitchHeight / 2,
        halfRoofSpan / 2
      );
      roofSouth.rotation.x = roofAngle;
      roofSouth.castShadow = true;
      roofSouth.receiveShadow = true;
      group.add(roofSouth);

      // Negative-Z roof slope.
      const roofNorth = new THREE.Mesh(
        new THREE.BoxGeometry(
          roofLength,
          roofThickness,
          roofPanelLength
        ),
        roofMat
      );

      roofNorth.position.set(
        0,
        wallTop + pitchHeight / 2,
        -halfRoofSpan / 2
      );
      roofNorth.rotation.x = -roofAngle;
      roofNorth.castShadow = true;
      roofNorth.receiveShadow = true;
      group.add(roofNorth);

      // Front and rear gable infill, exactly aligned with the wall ends.
      const gableShape = new THREE.Shape();
      gableShape.moveTo(-W / 2, 0);
      gableShape.lineTo(W / 2, 0);
      gableShape.lineTo(0, pitchHeight);
      gableShape.closePath();

      const gableGeometry = new THREE.ShapeGeometry(gableShape);
      const gableMaterial = wallMat.clone();

      const frontGable = new THREE.Mesh(gableGeometry, gableMaterial);
      frontGable.rotation.x = Math.PI / 2;
      frontGable.position.set(0, wallTop, W / 2 + 0.003);
      frontGable.castShadow = true;
      group.add(frontGable);

      const rearGable = new THREE.Mesh(
        gableGeometry.clone(),
        wallMat.clone()
      );

      rearGable.rotation.x = -Math.PI / 2;
      rearGable.position.set(0, wallTop, -W / 2 - 0.003);
      rearGable.castShadow = true;
      group.add(rearGable);
    } else {
      // Flat roof.
      const roofOverhang = 0.2;

      const flatRoof = new THREE.Mesh(
        new THREE.BoxGeometry(
          L + roofOverhang * 2,
          0.18,
          W + roofOverhang * 2
        ),
        new THREE.MeshStandardMaterial({
          color: 0x1e293b,
          roughness: 0.55,
          metalness: 0.2,
        })
      );

      flatRoof.position.y = wallTop + 0.09;
      flatRoof.castShadow = true;
      flatRoof.receiveShadow = true;
      group.add(flatRoof);
    }

    // South facade opening calculations.
    const facadeZ = W / 2 + 0.025;

    // Keep door/window dimensions valid for smaller shelters.
    const doorW = Math.min(0.85, L * 0.20);
    const doorH = Math.min(2.0, H * 0.78);

    const maxWindowWidth = Math.max(0.8, L * 0.42);
    const calculatedWindowWidth = Math.sqrt(glazingArea * 1.2);
    const winW = Math.min(
      maxWindowWidth,
      Math.max(0.8, calculatedWindowWidth)
    );

    const winH = Math.min(
      H * 0.55,
      Math.max(0.75, glazingArea / winW)
    );

    // Place door on left and window on right with a safe central gap.
    const doorX = -L * 0.32;
    const windowX = Math.min(
      L * 0.22,
      Math.max(0, L / 2 - winW / 2 - 0.15)
    );

    // If the shelter is narrow, keep both openings inside the facade.
    const safeDoorX = THREE.MathUtils.clamp(
      doorX,
      -L / 2 + doorW / 2 + 0.08,
      L / 2 - doorW / 2 - 0.08
    );

    const safeWindowX = THREE.MathUtils.clamp(
      windowX,
      -L / 2 + winW / 2 + 0.08,
      L / 2 - winW / 2 - 0.08
    );

    // Door.
    const door = new THREE.Mesh(
      new THREE.BoxGeometry(doorW, doorH, 0.05),
      new THREE.MeshStandardMaterial({
        color: 0x78350f,
        roughness: 0.72,
      })
    );

    door.position.set(
      safeDoorX,
      slabHeight + doorH / 2,
      facadeZ
    );
    door.castShadow = true;
    group.add(door);

    // Door frame.
    const doorFrameMat = new THREE.MeshStandardMaterial({
      color: 0x451a03,
      roughness: 0.65,
    });

    const doorFrame = new THREE.Mesh(
      new THREE.BoxGeometry(doorW + 0.08, doorH + 0.08, 0.035),
      doorFrameMat
    );

    doorFrame.position.set(
      safeDoorX,
      slabHeight + doorH / 2,
      W / 2 + 0.015
    );
    group.add(doorFrame);

    // Window glass.
    const glass = new THREE.Mesh(
      new THREE.PlaneGeometry(winW, winH),
      new THREE.MeshPhysicalMaterial({
        color: 0x38bdf8,
        transmission: 0.35,
        opacity: 0.78,
        transparent: true,
        roughness: 0.12,
        ior: 1.5,
        metalness: 0.08,
      })
    );

    const windowY = slabHeight + H * 0.58;

    glass.position.set(
      safeWindowX,
      windowY,
      facadeZ + 0.015
    );
    group.add(glass);

    // Window frame as four independent bars so the glass remains visible.
    const frameMat = new THREE.MeshStandardMaterial({
      color: 0x0f172a,
      roughness: 0.42,
    });

    const frameDepth = 0.06;
    const frameThickness = 0.07;

    const frameParts = [
      {
        size: [winW + frameThickness * 2, frameThickness, frameDepth],
        y: windowY + winH / 2 + frameThickness / 2,
        x: safeWindowX,
      },
      {
        size: [winW + frameThickness * 2, frameThickness, frameDepth],
        y: windowY - winH / 2 - frameThickness / 2,
        x: safeWindowX,
      },
      {
        size: [frameThickness, winH, frameDepth],
        y: windowY,
        x: safeWindowX - winW / 2 - frameThickness / 2,
      },
      {
        size: [frameThickness, winH, frameDepth],
        y: windowY,
        x: safeWindowX + winW / 2 + frameThickness / 2,
      },
    ];

    frameParts.forEach(({ size, x, y }) => {
      const frame = new THREE.Mesh(
        new THREE.BoxGeometry(size[0], size[1], size[2]),
        frameMat
      );

      frame.position.set(x, y, facadeZ + 0.035);
      group.add(frame);
    });

    // Simple centre mullion for architectural realism.
    const mullion = new THREE.Mesh(
      new THREE.BoxGeometry(frameThickness * 0.75, winH, frameDepth),
      frameMat
    );

    mullion.position.set(
      safeWindowX,
      windowY,
      facadeZ + 0.04
    );
    group.add(mullion);

    // North arrow. Keep it independent of facade openings.
    const arrowOrigin = new THREE.Vector3(L / 2 + 1.2, 0.05, 0);
    const arrowHelper = new THREE.ArrowHelper(
      new THREE.Vector3(0, 0, -1),
      arrowOrigin,
      1.5,
      0xef4444,
      0.4,
      0.2
    );
    group.add(arrowHelper);

    // Keep the complete shelter centered around the origin.
    // The orientation value is intentionally displayed by the UI/store;
    // the geometry itself is not rotated so the North reference remains stable.
    void orientation;
  }, [
    length,
    width,
    height,
    roofType,
    wallMaterial,
    windowArea,
    orientation,
  ]);

  return (
    <div
      className={`relative ${className} rounded-xl overflow-hidden eng-panel`}
    >
      <div
        ref={containerRef}
        className="w-full h-full cursor-grab active:cursor-grabbing"
      />

      {showLabels && (
        <div className="absolute top-3 left-3 bg-slate-900/80 backdrop-blur border border-slate-700/50 rounded-lg p-2.5 text-xs text-slate-300 pointer-events-none space-y-1 z-10 shadow-lg">
          <div className="font-semibold text-sky-400 flex items-center gap-1.5">
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Parametric Geometry Model
          </div>

          <div>
            Dimensions:{" "}
            <span className="text-white font-mono">
              {length.toFixed(1)}m × {width.toFixed(1)}m ×{" "}
              {height.toFixed(1)}m
            </span>
          </div>

          <div>
            Floor Area:{" "}
            <span className="text-white font-mono">
              {(length * width).toFixed(1)} m²
            </span>{" "}
            | Vol:{" "}
            <span className="text-white font-mono">
              {(length * width * height).toFixed(1)} m³
            </span>
          </div>

          <div>
            Roof:{" "}
            <span className="text-sky-300 font-mono capitalize">
              {roofType}
            </span>{" "}
            | South Glazing:{" "}
            <span className="text-sky-300 font-mono">
              {windowArea.toFixed(1)} m²
            </span>
          </div>
        </div>
      )}

      <div className="absolute bottom-3 right-3 bg-slate-900/80 backdrop-blur border border-slate-700/50 rounded-lg px-2.5 py-1 text-[11px] text-slate-400 pointer-events-none z-10">
        🖱️ Drag to Orbit · Scroll to Zoom
      </div>

      <div className="absolute top-3 right-3 bg-slate-900/80 backdrop-blur border border-rose-500/30 rounded-lg px-2.5 py-1 text-[11px] font-semibold text-rose-400 pointer-events-none z-10 flex items-center gap-1">
        <span>↑</span>
        <span>NORTH</span>
      </div>
    </div>
  );
};
