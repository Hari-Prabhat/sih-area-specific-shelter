import { useRef, useMemo, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Environment, ContactShadows, Float, Html, Text } from '@react-three/drei';
import * as THREE from 'three';
import { ShelterDesign } from '../types';

/* ─── colour palette for materials ─── */
const MATERIAL_COLORS: Record<string, { wall: string; accent: string }> = {
  'Mud/Adobe':                           { wall: '#b08968', accent: '#8B6E4E' },
  'Stone (Granite)':                     { wall: '#8c8c8c', accent: '#666666' },
  'Stone (Limestone)':                   { wall: '#d4c5a9', accent: '#b8a88a' },
  'Timber/Wood':                         { wall: '#a0714f', accent: '#7a5230' },
  'Bamboo Composite':                    { wall: '#c4a35a', accent: '#9e8040' },
  'Brick (Solid)':                       { wall: '#c25840', accent: '#a04030' },
  'Concrete (Dense)':                    { wall: '#a0a0a0', accent: '#808080' },
  'Concrete (Lightweight)':              { wall: '#b8b8b0', accent: '#989890' },
  'Steel Sheet':                         { wall: '#b0b8c8', accent: '#8090a8' },
  'Glass (Clear)':                       { wall: '#c8dce8', accent: '#a0bcd0' },
  'AAC Block (Autoclaved Aerated Concrete)': { wall: '#e0ddd5', accent: '#c4c0b8' },
  'SIP Panel (Structural Insulated Panel)':  { wall: '#d8cfc0', accent: '#b8b0a0' },
  'Rammed Earth (Stabilized)':           { wall: '#c4956a', accent: '#a07850' },
  'Phase Change Material (PCM) Wall':    { wall: '#7ec8e3', accent: '#5898b8' },
  'Trombe Wall (Concrete + Glass)':      { wall: '#98a8a0', accent: '#708880' },
};

function getColors(materialName: string) {
  return MATERIAL_COLORS[materialName] ?? { wall: '#b08968', accent: '#8B6E4E' };
}

/* ─── animated ground grid ─── */
function GroundGrid() {
  return (
    <group>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]} receiveShadow>
        <planeGeometry args={[40, 40]} />
        <meshStandardMaterial color="#1a2332" transparent opacity={0.6} />
      </mesh>
      <gridHelper args={[40, 40, '#2a3a4a', '#1e2e3e']} position={[0, 0, 0]} />
    </group>
  );
}

/**
 * Static Geographic Compass Rose
 * Convention:
 *   North = -Z (0° Azimuth)
 *   East  = +X (90° Azimuth)
 *   South = +Z (180° Azimuth - Solar Equator Facing)
 *   West  = -X (270° Azimuth)
 * The compass remains geographically fixed. The building rotates by (orientation - 180°).
 */
function StaticCompass() {
  return (
    <group position={[0, 0.02, 0]}>
      {/* North Pointer Arrow (-Z) */}
      <mesh position={[0, 0.01, -8]}>
        <coneGeometry args={[0.35, 0.9, 4]} />
        <meshStandardMaterial color="#ef4444" emissive="#ef4444" emissiveIntensity={0.5} />
      </mesh>
      <Text position={[0, 0.5, -9]} fontSize={0.55} color="#ef4444" anchorX="center" anchorY="middle" fontWeight="bold">
        N (0°)
      </Text>
      {/* South Marker (+Z) */}
      <Text position={[0, 0.5, 9]} fontSize={0.45} color="#38bdf8" anchorX="center" anchorY="middle" fontWeight="bold">
        S (180° Solar)
      </Text>
      {/* East Marker (+X) */}
      <Text position={[9, 0.5, 0]} fontSize={0.4} color="#64748b" anchorX="center" anchorY="middle">
        E (90°)
      </Text>
      {/* West Marker (-X) */}
      <Text position={[-9, 0.5, 0]} fontSize={0.4} color="#64748b" anchorX="center" anchorY="middle">
        W (270°)
      </Text>
      {/* Cardinal Ring */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.005, 0]}>
        <ringGeometry args={[7.8, 8.0, 64]} />
        <meshBasicMaterial color="#334155" transparent opacity={0.4} side={THREE.DoubleSide} />
      </mesh>
    </group>
  );
}

/* ─── window with architectural frame trim ─── */
function FramedWindow({ position, rotation, width, height }: {
  position: [number, number, number]; rotation: [number, number, number];
  width: number; height: number;
}) {
  const frameThick = 0.05;
  const frameDepth = 0.06;

  return (
    <group position={position} rotation={rotation}>
      {/* Glass Pane */}
      <mesh castShadow>
        <planeGeometry args={[width, height]} />
        <meshPhysicalMaterial
          color="#88ccee"
          transparent
          opacity={0.45}
          roughness={0.05}
          metalness={0.1}
          transmission={0.75}
          thickness={0.04}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* Outer Metallic Window Frame */}
      {/* Top frame */}
      <mesh position={[0, height / 2 + frameThick / 2, 0.01]}>
        <boxGeometry args={[width + frameThick * 2, frameThick, frameDepth]} />
        <meshStandardMaterial color="#1e293b" roughness={0.4} metalness={0.6} />
      </mesh>
      {/* Bottom sill */}
      <mesh position={[0, -height / 2 - frameThick / 2, 0.015]}>
        <boxGeometry args={[width + frameThick * 2 + 0.04, frameThick, frameDepth + 0.03]} />
        <meshStandardMaterial color="#334155" roughness={0.4} metalness={0.5} />
      </mesh>
      {/* Left stile */}
      <mesh position={[-width / 2 - frameThick / 2, 0, 0.01]}>
        <boxGeometry args={[frameThick, height, frameDepth]} />
        <meshStandardMaterial color="#1e293b" roughness={0.4} metalness={0.6} />
      </mesh>
      {/* Right stile */}
      <mesh position={[width / 2 + frameThick / 2, 0, 0.01]}>
        <boxGeometry args={[frameThick, height, frameDepth]} />
        <meshStandardMaterial color="#1e293b" roughness={0.4} metalness={0.6} />
      </mesh>
      {/* Mullion vertical divider if width > 1.2m */}
      {width > 1.2 && (
        <mesh position={[0, 0, 0.01]}>
          <boxGeometry args={[0.03, height, frameDepth * 0.8]} />
          <meshStandardMaterial color="#1e293b" roughness={0.4} metalness={0.6} />
        </mesh>
      )}
    </group>
  );
}

/* ─── parametric door responsive to doorArea ─── */
function ParametricDoor({ position, rotation, doorArea }: {
  position: [number, number, number]; rotation: [number, number, number];
  doorArea: number;
}) {
  // Deterministic calculation: aspect ratio ~2.2, bounded within realistic doors
  const area = Math.max(0.8, Math.min(5.0, doorArea || 2.0));
  const rawWidth = Math.sqrt(area / 2.2);
  const doorWidth = Math.max(0.8, Math.min(1.8, Math.round(rawWidth * 100) / 100));
  const doorHeight = Math.max(1.9, Math.min(2.5, Math.round((area / doorWidth) * 100) / 100));

  const frameThick = 0.06;

  return (
    <group position={position} rotation={rotation}>
      {/* Door Leaf */}
      <mesh position={[0, doorHeight / 2, 0]} castShadow>
        <boxGeometry args={[doorWidth, doorHeight, 0.08]} />
        <meshStandardMaterial color="#4a2e1b" roughness={0.7} />
      </mesh>

      {/* Surrounding Architrave Frame */}
      <mesh position={[0, doorHeight + frameThick / 2, 0.01]}>
        <boxGeometry args={[doorWidth + frameThick * 2, frameThick, 0.10]} />
        <meshStandardMaterial color="#1e293b" roughness={0.4} metalness={0.6} />
      </mesh>
      <mesh position={[-doorWidth / 2 - frameThick / 2, doorHeight / 2, 0.01]}>
        <boxGeometry args={[frameThick, doorHeight, 0.10]} />
        <meshStandardMaterial color="#1e293b" roughness={0.4} metalness={0.6} />
      </mesh>
      <mesh position={[doorWidth / 2 + frameThick / 2, doorHeight / 2, 0.01]}>
        <boxGeometry args={[frameThick, doorHeight, 0.10]} />
        <meshStandardMaterial color="#1e293b" roughness={0.4} metalness={0.6} />
      </mesh>

      {/* Brass Handle */}
      <mesh position={[doorWidth * 0.35, doorHeight * 0.48, 0.05]}>
        <sphereGeometry args={[0.04, 16, 16]} />
        <meshStandardMaterial color="#d4a520" metalness={0.85} roughness={0.2} />
      </mesh>

      {/* Vision glass panel if door is wide */}
      {doorWidth > 1.0 && (
        <mesh position={[0, doorHeight * 0.7, 0.01]}>
          <planeGeometry args={[doorWidth * 0.4, doorHeight * 0.3]} />
          <meshPhysicalMaterial color="#88ccee" transparent opacity={0.4} transmission={0.7} side={THREE.DoubleSide} />
        </mesh>
      )}
    </group>
  );
}

/* ─── dimension label ─── */
function DimensionLabel({ start, end, label, offset = 0.5 }: {
  start: [number, number, number]; end: [number, number, number]; label: string; offset?: number;
}) {
  const mid: [number, number, number] = [
    (start[0] + end[0]) / 2,
    (start[1] + end[1]) / 2 + offset,
    (start[2] + end[2]) / 2,
  ];
  return (
    <group>
      <Text position={mid} fontSize={0.35} color="#f59e0b" anchorX="center" anchorY="middle"
        outlineWidth={0.02} outlineColor="#000000">
        {label}
      </Text>
    </group>
  );
}

/**
 * ═══════════════════════════════════════════════════
 * RECTANGULAR SHELTER WITH ARCHITECTURAL PARAMETRIC ROOF
 * ═══════════════════════════════════════════════════
 * Geometry:
 *   Length (L) spans along X-axis
 *   Width (W) spans along Z-axis
 *   Eave/Wall Height (H) along Y-axis
 *   Pitch Angle (θ)
 *   halfSpan = W / 2
 *   ridgeRise = halfSpan * tan(θ)
 *   ridgeHeight = H + ridgeRise
 *   Overhang = 0.20m beyond wall plate
 */
function RectangularShelter({ design, wallColor, accentColor }: {
  design: ShelterDesign; wallColor: string; accentColor: string;
}) {
  const {
    length,
    width,
    height,
    roofAngle,
    wallThickness,
    windowArea = 3.0,
    doorArea = 2.0,
    insulationType,
    thermalMassEnabled,
  } = design;

  const roofRad = ((roofAngle || 0) * Math.PI) / 180;
  const isPitched = roofAngle && roofAngle > 0;
  const halfSpan = width / 2;
  const ridgeRise = isPitched ? Math.tan(roofRad) * halfSpan : 0.0;
  const ridgeHeight = height + ridgeRise;

  const overhang = 0.22;
  const roofThick = 0.12;

  // Window geometry rule:
  // Allocate total window area across 2 front windows (South / +Z) and 1 rear window (North / -Z)
  // Front gets 70% of glazing, rear gets 30%
  const frontGlazingTotal = windowArea * 0.7;
  const rearGlazingTotal = windowArea * 0.3;
  const singleFrontArea = Math.max(0.3, frontGlazingTotal / 2);
  const winW = Math.max(0.6, Math.min(2.4, Math.round(Math.sqrt(singleFrontArea * 1.3) * 100) / 100));
  const winH = Math.max(0.6, Math.min(2.0, Math.round((singleFrontArea / winW) * 100) / 100));

  const rearW = Math.max(0.5, Math.min(1.8, Math.round(Math.sqrt(rearGlazingTotal * 1.2) * 100) / 100));
  const rearH = Math.max(0.5, Math.min(1.6, Math.round((rearGlazingTotal / rearW) * 100) / 100));

  const hasInsulation = Boolean(insulationType && insulationType !== 'None');

  /* Triangular Gable Geometry Builder for Left (-X) and Right (+X) Wall Tops */
  const gableGeometry = useMemo(() => {
    if (!isPitched || ridgeRise <= 0.001) return null;

    // Create 3D triangular prism for gable wall with thickness = wallThickness
    const halfThick = wallThickness / 2;
    // Vertices for a prism with triangular base in Z-Y plane, extruded along X
    // Apex: (0, ridgeHeight, 0)
    // Front eave: (0, height, halfSpan)
    // Back eave:  (0, height, -halfSpan)
    const vertices = new Float32Array([
      // Front face (+X side of prism)
      halfThick, height, halfSpan,
      halfThick, height, -halfSpan,
      halfThick, ridgeHeight, 0,

      // Back face (-X side of prism)
      -halfThick, height, -halfSpan,
      -halfThick, height, halfSpan,
      -halfThick, ridgeHeight, 0,

      // Slope face 1 (+Z slope)
      -halfThick, height, halfSpan,
      halfThick, height, halfSpan,
      halfThick, ridgeHeight, 0,
      -halfThick, height, halfSpan,
      halfThick, ridgeHeight, 0,
      -halfThick, ridgeHeight, 0,

      // Slope face 2 (-Z slope)
      halfThick, height, -halfSpan,
      -halfThick, height, -halfSpan,
      halfThick, ridgeHeight, 0,
      -halfThick, height, -halfSpan,
      -halfThick, ridgeHeight, 0,
      halfThick, ridgeHeight, 0,

      // Bottom face
      -halfThick, height, halfSpan,
      -halfThick, height, -halfSpan,
      halfThick, height, halfSpan,
      halfThick, height, halfSpan,
      -halfThick, height, -halfSpan,
      halfThick, height, -halfSpan,
    ]);

    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
    geo.computeVertexNormals();
    return geo;
  }, [isPitched, height, ridgeHeight, halfSpan, wallThickness, ridgeRise]);

  /* Parametric Pitched Roof Geometry (Solid, continuous gable roof with eaves overhang) */
  const pitchedRoofGeometry = useMemo(() => {
    if (!isPitched || ridgeRise <= 0.001) return null;

    const halfL = length / 2 + overhang;
    const eaveZ = halfSpan + overhang;
    const slopeHyp = Math.sqrt(Math.pow(eaveZ, 2) + Math.pow(ridgeRise, 2));

    // Two monolithic sloping slabs meeting tightly at ridge (Z=0, Y=ridgeHeight)
    // We compute roof plane positions and rotations exactly:
    // Left slope (+Z side): eave at +eaveZ, ridge at Z=0
    // Angle of slope = roofRad
    return {
      slopeLength: slopeHyp,
      roofLength: halfL * 2,
    };
  }, [isPitched, length, halfSpan, ridgeRise, overhang]);

  return (
    <group>
      {/* ── 1. BASE WALLS ── */}
      {/* South Facade (Front, +Z) */}
      <mesh position={[0, height / 2, halfSpan]} castShadow receiveShadow>
        <boxGeometry args={[length, height, wallThickness]} />
        <meshStandardMaterial color={wallColor} roughness={0.8} />
      </mesh>
      {/* North Facade (Back, -Z) */}
      <mesh position={[0, height / 2, -halfSpan]} castShadow receiveShadow>
        <boxGeometry args={[length, height, wallThickness]} />
        <meshStandardMaterial color={wallColor} roughness={0.8} />
      </mesh>
      {/* West Wall (Left, -X) */}
      <mesh position={[-length / 2, height / 2, 0]} castShadow receiveShadow>
        <boxGeometry args={[wallThickness, height, width]} />
        <meshStandardMaterial color={wallColor} roughness={0.8} />
      </mesh>
      {/* East Wall (Right, +X) */}
      <mesh position={[length / 2, height / 2, 0]} castShadow receiveShadow>
        <boxGeometry args={[wallThickness, height, width]} />
        <meshStandardMaterial color={wallColor} roughness={0.8} />
      </mesh>

      {/* ── 2. TRIANGULAR GABLE WALL INFILLS (Seals ends completely) ── */}
      {isPitched && gableGeometry && (
        <>
          <mesh geometry={gableGeometry} position={[-length / 2, 0, 0]} castShadow receiveShadow>
            <meshStandardMaterial color={wallColor} roughness={0.8} />
          </mesh>
          <mesh geometry={gableGeometry} position={[length / 2, 0, 0]} castShadow receiveShadow>
            <meshStandardMaterial color={wallColor} roughness={0.8} />
          </mesh>
        </>
      )}

      {/* ── 3. ARCHITECTURAL ROOF SYSTEM ── */}
      {isPitched ? (
        <group>
          {/* Front Sloping Roof Plane (+Z pitch down from ridge) */}
          <mesh
            position={[
              0,
              height + ridgeRise / 2,
              (halfSpan + overhang) / 2 - overhang * 0.5,
            ]}
            rotation={[roofRad, 0, 0]}
            castShadow
            receiveShadow
          >
            <boxGeometry
              args={[
                length + overhang * 2,
                (halfSpan + overhang) / Math.cos(roofRad),
                roofThick,
              ]}
            />
            <meshStandardMaterial color={accentColor} roughness={0.5} />
          </mesh>

          {/* Rear Sloping Roof Plane (-Z pitch down from ridge) */}
          <mesh
            position={[
              0,
              height + ridgeRise / 2,
              -((halfSpan + overhang) / 2 - overhang * 0.5),
            ]}
            rotation={[-roofRad, 0, 0]}
            castShadow
            receiveShadow
          >
            <boxGeometry
              args={[
                length + overhang * 2,
                (halfSpan + overhang) / Math.cos(roofRad),
                roofThick,
              ]}
            />
            <meshStandardMaterial color={accentColor} roughness={0.5} />
          </mesh>

          {/* Weatherproof Ridge Cap Beam */}
          <mesh position={[0, ridgeHeight + roofThick * 0.35, 0]} castShadow>
            <boxGeometry args={[length + overhang * 2 + 0.05, roofThick * 0.8, 0.18]} />
            <meshStandardMaterial color="#334155" roughness={0.4} metalness={0.7} />
          </mesh>
        </group>
      ) : (
        /* Flat Roof Construction when roofAngle === 0 */
        <mesh position={[0, height + roofThick / 2, 0]} castShadow receiveShadow>
          <boxGeometry args={[length + overhang * 2, roofThick, width + overhang * 2]} />
          <meshStandardMaterial color={accentColor} roughness={0.5} />
        </mesh>
      )}

      {/* ── 4. INSULATION LAYER VISUALIZATION ── */}
      {hasInsulation && (
        <mesh position={[0, height / 2, 0]}>
          <boxGeometry args={[length + 0.15, height + 0.05, width + 0.15]} />
          <meshStandardMaterial color="#eab308" transparent opacity={0.12} wireframe />
        </mesh>
      )}

      {/* ── 5. STRUCTURAL FLOOR SLAB ── */}
      <mesh position={[0, 0.05, 0]} receiveShadow>
        <boxGeometry args={[length + 0.3, 0.1, width + 0.3]} />
        <meshStandardMaterial color="#334155" roughness={0.9} />
      </mesh>

      {/* ── 6. THERMAL MASS INTERNAL STORAGE CORE ── */}
      {thermalMassEnabled && (
        <mesh position={[0, 0.11, 0]} receiveShadow>
          <boxGeometry args={[length * 0.75, 0.05, width * 0.75]} />
          <meshStandardMaterial color="#2563eb" roughness={0.4} opacity={0.8} transparent />
        </mesh>
      )}

      {/* ── 7. PARAMETRIC SOLAR WINDOWS (SOUTH FACADE +Z) ── */}
      <FramedWindow
        position={[-length / 4, height * 0.52, halfSpan + wallThickness / 2 + 0.01]}
        rotation={[0, 0, 0]}
        width={winW}
        height={winH}
      />
      <FramedWindow
        position={[length / 4, height * 0.52, halfSpan + wallThickness / 2 + 0.01]}
        rotation={[0, 0, 0]}
        width={winW}
        height={winH}
      />

      {/* ── 8. PARAMETRIC REAR WINDOW (NORTH FACADE -Z) ── */}
      <FramedWindow
        position={[0, height * 0.52, -(halfSpan + wallThickness / 2 + 0.01)]}
        rotation={[0, Math.PI, 0]}
        width={rearW}
        height={rearH}
      />

      {/* ── 9. PARAMETRIC ACCESS DOOR (SOUTH FACADE +Z) ── */}
      <ParametricDoor
        position={[0, 0, halfSpan + wallThickness / 2 + 0.01]}
        rotation={[0, 0, 0]}
        doorArea={doorArea}
      />

      {/* ── 10. CAD DIMENSION CALLOUT LABELS ── */}
      <DimensionLabel
        start={[-length / 2, 0, halfSpan + 1.6]}
        end={[length / 2, 0, halfSpan + 1.6]}
        label={`L = ${length.toFixed(1)}m`}
        offset={0.3}
      />
      <DimensionLabel
        start={[length / 2 + 1.6, 0, -halfSpan]}
        end={[length / 2 + 1.6, 0, halfSpan]}
        label={`W = ${width.toFixed(1)}m`}
        offset={0.3}
      />
      <DimensionLabel
        start={[length / 2 + 1.2, 0, halfSpan]}
        end={[length / 2 + 1.2, height, halfSpan]}
        label={`H = ${height.toFixed(1)}m (Ridge: ${ridgeHeight.toFixed(1)}m)`}
        offset={0}
      />
    </group>
  );
}

/* ═══════════════════════════════════════════════════
   CYLINDRICAL SHELTER
   ═══════════════════════════════════════════════════ */
function CylindricalShelter({ design, wallColor, accentColor }: {
  design: ShelterDesign; wallColor: string; accentColor: string;
}) {
  const r = Math.sqrt((design.length * design.width) / Math.PI);
  const h = design.height;

  return (
    <group>
      {/* main cylinder */}
      <mesh position={[0, h / 2, 0]} castShadow receiveShadow>
        <cylinderGeometry args={[r, r, h, 48, 1, true]} />
        <meshStandardMaterial color={wallColor} roughness={0.8} side={THREE.DoubleSide} />
      </mesh>
      {/* conical roof if pitched, else flat disc */}
      {design.roofAngle && design.roofAngle > 0 ? (
        <mesh position={[0, h + (r * Math.tan((design.roofAngle * Math.PI) / 180)) / 2, 0]} castShadow>
          <coneGeometry args={[r + 0.2, r * Math.tan((design.roofAngle * Math.PI) / 180), 48]} />
          <meshStandardMaterial color={accentColor} roughness={0.6} />
        </mesh>
      ) : (
        <mesh position={[0, h, 0]} castShadow>
          <cylinderGeometry args={[r + 0.15, r + 0.15, 0.15, 48]} />
          <meshStandardMaterial color={accentColor} roughness={0.6} />
        </mesh>
      )}
      {/* floor */}
      <mesh position={[0, 0.05, 0]} receiveShadow>
        <cylinderGeometry args={[r + 0.1, r + 0.1, 0.1, 48]} />
        <meshStandardMaterial color="#4a4a48" roughness={0.9} />
      </mesh>
      {/* windows */}
      <FramedWindow position={[0, h / 2, r + 0.05]} rotation={[0, 0, 0]} width={1.2} height={1.0} />
      <FramedWindow position={[r + 0.05, h / 2, 0]} rotation={[0, Math.PI / 2, 0]} width={1.2} height={1.0} />
      {/* door */}
      <ParametricDoor position={[0, 0, r + 0.05]} rotation={[0, 0, 0]} doorArea={design.doorArea} />
      {/* labels */}
      <DimensionLabel start={[0, 0, 0]} end={[r, 0, 0]} label={`Radius = ${r.toFixed(1)}m`} offset={0.3} />
      <DimensionLabel start={[r + 1, 0, 0]} end={[r + 1, h, 0]} label={`H = ${h}m`} offset={0} />
    </group>
  );
}

/* ═══════════════════════════════════════════════════
   DOME SHELTER
   ═══════════════════════════════════════════════════ */
function DomeShelter({ design, wallColor, accentColor }: {
  design: ShelterDesign; wallColor: string; accentColor: string;
}) {
  const r = Math.sqrt((design.length * design.width) / Math.PI);
  const h = design.height;

  return (
    <group>
      {/* dome shell */}
      <mesh position={[0, 0, 0]} castShadow receiveShadow>
        <sphereGeometry args={[r, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2]} />
        <meshStandardMaterial color={wallColor} roughness={0.7} side={THREE.DoubleSide} />
      </mesh>
      {/* secondary translucent dome highlight */}
      <mesh position={[0, 0, 0]}>
        <sphereGeometry args={[r + 0.05, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2]} />
        <meshStandardMaterial color={accentColor} transparent opacity={0.1} side={THREE.DoubleSide} />
      </mesh>
      {/* floor */}
      <mesh position={[0, 0.05, 0]} receiveShadow>
        <cylinderGeometry args={[r + 0.1, r + 0.1, 0.1, 48]} />
        <meshStandardMaterial color="#4a4a48" roughness={0.9} />
      </mesh>
      {/* door opening frame */}
      <ParametricDoor position={[0, 0, r - 0.05]} rotation={[0, 0, 0]} doorArea={design.doorArea} />
      {/* windows */}
      <FramedWindow position={[r * 0.7, r * 0.5, r * 0.7]} rotation={[0, Math.PI / 4, 0]} width={0.9} height={0.7} />
      <FramedWindow position={[-r * 0.7, r * 0.5, r * 0.7]} rotation={[0, -Math.PI / 4, 0]} width={0.9} height={0.7} />
      {/* labels */}
      <DimensionLabel start={[0, 0, 0]} end={[r, 0, 0]} label={`Radius = ${r.toFixed(1)}m`} offset={0.3} />
      <DimensionLabel start={[r + 1, 0, 0]} end={[r + 1, r, 0]} label={`H = ${h}m`} offset={0} />
    </group>
  );
}

/* ═══════════════════════════════════════════════════
   PYRAMID SHELTER
   ═══════════════════════════════════════════════════ */
function PyramidShelter({ design, wallColor, accentColor }: {
  design: ShelterDesign; wallColor: string; accentColor: string;
}) {
  const { length, width, height, doorArea = 2.0 } = design;

  const vertices = useMemo(() => {
    const topScale = 0.15;
    const tl = length * topScale;
    const tw = width * topScale;
    return new Float32Array([
      // base quad
      -length / 2, 0, -width / 2,   length / 2, 0, -width / 2,   length / 2, 0, width / 2,
      -length / 2, 0, -width / 2,   length / 2, 0, width / 2,    -length / 2, 0, width / 2,
      // front face
      -length / 2, 0, width / 2,    length / 2, 0, width / 2,    tl, height, tw,
      -length / 2, 0, width / 2,    tl, height, tw,               -tl, height, tw,
      // back face
      length / 2, 0, -width / 2,    -length / 2, 0, -width / 2,  -tl, height, -tw,
      length / 2, 0, -width / 2,    -tl, height, -tw,             tl, height, -tw,
      // right face
      length / 2, 0, width / 2,     length / 2, 0, -width / 2,   tl, height, -tw,
      length / 2, 0, width / 2,     tl, height, -tw,              tl, height, tw,
      // left face
      -length / 2, 0, -width / 2,   -length / 2, 0, width / 2,   -tl, height, tw,
      -length / 2, 0, -width / 2,   -tl, height, tw,              -tl, height, -tw,
      // top face
      -tl, height, -tw,  tl, height, -tw,  tl, height, tw,
      -tl, height, -tw,  tl, height, tw,   -tl, height, tw,
    ]);
  }, [length, width, height]);

  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
    geo.computeVertexNormals();
    return geo;
  }, [vertices]);

  return (
    <group>
      <mesh geometry={geometry} castShadow receiveShadow>
        <meshStandardMaterial color={wallColor} roughness={0.8} side={THREE.DoubleSide} />
      </mesh>
      <mesh geometry={geometry}>
        <meshStandardMaterial color={accentColor} transparent opacity={0.15} wireframe side={THREE.DoubleSide} />
      </mesh>
      <mesh position={[0, 0.05, 0]} receiveShadow>
        <boxGeometry args={[length + 0.2, 0.1, width + 0.2]} />
        <meshStandardMaterial color="#4a4a48" roughness={0.9} />
      </mesh>
      <ParametricDoor position={[0, 0, width / 2 + 0.06]} rotation={[0, 0, 0]} doorArea={doorArea} />
      <DimensionLabel start={[-length / 2, 0, width / 2 + 1.5]} end={[length / 2, 0, width / 2 + 1.5]}
        label={`L = ${length}m`} offset={0.3} />
      <DimensionLabel start={[length / 2 + 1.5, 0, -width / 2]} end={[length / 2 + 1.5, 0, width / 2]}
        label={`W = ${width}m`} offset={0.3} />
      <DimensionLabel start={[length / 2 + 1, 0, width / 2]} end={[length / 2 + 1, height, width / 2]}
        label={`H = ${height}m`} offset={0} />
    </group>
  );
}

/* ─── animated sun position ─── */
function SunLight() {
  const ref = useRef<THREE.DirectionalLight>(null!);
  useFrame(({ clock }) => {
    const t = clock.getElapsedTime() * 0.1;
    ref.current.position.set(Math.cos(t) * 15, 12, Math.sin(t) * 15);
  });
  return (
    <directionalLight ref={ref} intensity={1.8} castShadow color="#fff5e0"
      shadow-mapSize-width={2048} shadow-mapSize-height={2048}
      shadow-camera-far={50} shadow-camera-left={-15} shadow-camera-right={15}
      shadow-camera-top={15} shadow-camera-bottom={-15}
    />
  );
}

/* ─── thermal glow indicator ─── */
function ThermalGlow({ comfortIndex }: { comfortIndex: number }) {
  const ref = useRef<THREE.PointLight>(null!);
  const color = comfortIndex >= 70 ? '#22c55e' : comfortIndex >= 50 ? '#eab308' : '#ef4444';
  const intensity = 0.3 + (comfortIndex / 100) * 0.7;

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (ref.current) {
      ref.current.intensity = intensity + Math.sin(t * 2) * 0.15;
    }
  });

  return <pointLight ref={ref} position={[0, 2, 0]} color={color} intensity={intensity} distance={12} />;
}

/* ─── info badge floating above shelter ─── */
function InfoBadge({ design, comfortIndex, avgTemp }: {
  design: ShelterDesign; comfortIndex?: number; avgTemp?: number;
}) {
  const yPos = design.height + 2.5;
  return (
    <Float speed={2} rotationIntensity={0} floatIntensity={0.3}>
      <Html position={[0, yPos, 0]} center transform={false} style={{ pointerEvents: 'none' }}>
        <div style={{
          background: 'linear-gradient(135deg, rgba(30,41,59,0.95), rgba(15,23,42,0.95))',
          border: '1px solid rgba(245,158,11,0.3)',
          borderRadius: '12px',
          padding: '10px 16px',
          color: 'white',
          fontSize: '11px',
          fontFamily: 'Inter, system-ui, sans-serif',
          minWidth: '140px',
          textAlign: 'center',
          backdropFilter: 'blur(8px)',
          boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
        }}>
          <div style={{ fontWeight: 700, fontSize: '13px', color: '#f59e0b', marginBottom: '4px' }}>
            {design.shape.charAt(0).toUpperCase() + design.shape.slice(1)} Shelter
          </div>
          <div style={{ color: '#94a3b8' }}>
            {design.length} × {design.width} × {design.height}m
          </div>
          {comfortIndex !== undefined && (
            <div style={{ marginTop: '4px', color: comfortIndex >= 70 ? '#22c55e' : comfortIndex >= 50 ? '#eab308' : '#ef4444' }}>
              Comfort: {comfortIndex}%
            </div>
          )}
          {avgTemp !== undefined && (
            <div style={{ color: '#60a5fa' }}>Avg Inside: {avgTemp}°C</div>
          )}
        </div>
      </Html>
    </Float>
  );
}

/**
 * ═══════════════════════════════════════════════════
 * MAIN 3D SCENE
 * ═══════════════════════════════════════════════════
 * Coordinate Frame:
 *   Static Geographic Compass:
 *     North = -Z (0°)
 *     East  = +X (90°)
 *     South = +Z (180° Solar Equator)
 *     West  = -X (270°)
 *
 * Shelter Orientation:
 *   The shelter's principal solar aperture faces South (+Z) when orientation === 180°.
 *   The shelter group rotates by (design.orientation - 180°) around Y-axis.
 *   This rotates the building with respect to fixed geographic coordinates.
 */
function ShelterScene({ design, materialName, comfortIndex, avgTemp }: {
  design: ShelterDesign; materialName: string; comfortIndex?: number; avgTemp?: number;
}) {
  const colors = getColors(materialName);
  const shelterGroupRef = useRef<THREE.Group>(null!);

  // Orientation angle in radians: building rotates relative to static compass
  // When orientation === 180 (South), rotation is 0 rad (facade faces +Z).
  const shelterRotationY = -(((design.orientation ?? 180) - 180) * Math.PI) / 180;

  const shelterProps = { design, wallColor: colors.wall, accentColor: colors.accent };

  return (
    <>
      <ambientLight intensity={0.4} />
      <SunLight />
      <pointLight position={[-8, 8, -8]} intensity={0.4} color="#b0c4de" />
      {comfortIndex !== undefined && <ThermalGlow comfortIndex={comfortIndex} />}

      {/* 1. FIXED GEOGRAPHIC COMPASS & GROUND (Does NOT rotate with building) */}
      <StaticCompass />
      <GroundGrid />

      {/* 2. ROTATING SHELTER ASSEMBLY (Rotates to true solar azimuth) */}
      <group ref={shelterGroupRef} rotation={[0, shelterRotationY, 0]}>
        {design.shape === 'rectangular' && <RectangularShelter {...shelterProps} />}
        {design.shape === 'cylindrical' && <CylindricalShelter {...shelterProps} />}
        {design.shape === 'dome' && <DomeShelter {...shelterProps} />}
        {design.shape === 'pyramid' && <PyramidShelter {...shelterProps} />}

        <InfoBadge design={design} comfortIndex={comfortIndex} avgTemp={avgTemp} />
      </group>

      <ContactShadows position={[0, -0.01, 0]} opacity={0.35} scale={30} blur={2} far={10} color="#000020" />
      <Environment preset="sunset" />
      <OrbitControls
        makeDefault
        minPolarAngle={0.2}
        maxPolarAngle={Math.PI / 2.05}
        minDistance={5}
        maxDistance={32}
        enablePan
        target={[0, design.height / 2, 0]}
      />
    </>
  );
}

/* ═══════════════════════════════════════════════════
   EXPORTED COMPONENT
   ═══════════════════════════════════════════════════ */
interface ShelterModel3DProps {
  design: ShelterDesign;
  materialName: string;
  comfortIndex?: number;
  avgTemp?: number;
}

export default function ShelterModel3D({ design, materialName, comfortIndex, avgTemp }: ShelterModel3DProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);

  const cameraPos: [number, number, number] = useMemo(() => {
    const maxDim = Math.max(design.length, design.width, design.height);
    const dist = maxDim * 1.8;
    return [dist, dist * 0.8, dist];
  }, [design.length, design.width, design.height]);

  return (
    <div className={`relative ${isFullscreen ? 'fixed inset-0 z-[100] bg-slate-900' : ''}`}>
      <div className={`bg-gradient-to-br from-slate-900 via-[#0f172a] to-slate-800 rounded-xl border border-slate-700/30 overflow-hidden ${
        isFullscreen ? 'h-full rounded-none' : ''
      }`}>
        {/* toolbar */}
        <div className="flex items-center justify-between px-4 py-2.5 bg-slate-800/80 border-b border-slate-700/30">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            <span className="text-xs font-semibold text-slate-300">3D Shelter Visualization</span>
            <span className="text-[10px] px-2 py-0.5 bg-amber-500/20 text-amber-400 rounded-full font-medium">
              Parametric CAD Model
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-[11px] text-slate-400 font-mono">
              Azimuth: <strong className="text-amber-400">{design.orientation}°</strong> | Roof Pitch: <strong className="text-cyan-400">{design.roofAngle || 0}°</strong>
            </span>
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="text-xs text-slate-400 hover:text-white px-2 py-1 rounded bg-slate-700/50 hover:bg-slate-700"
            >
              {isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
            </button>
          </div>
        </div>

        {/* 3D Canvas */}
        <div className={isFullscreen ? 'h-[calc(100vh-45px)]' : 'h-[360px]'}>
          <Canvas
            camera={{ position: cameraPos, fov: 45 }}
            shadows
            gl={{ antialias: true, alpha: false }}
          >
            <ShelterScene
              design={design}
              materialName={materialName}
              comfortIndex={comfortIndex}
              avgTemp={avgTemp}
            />
          </Canvas>
        </div>

        {/* Caption footer */}
        <div className="px-4 py-2 bg-slate-900/90 border-t border-slate-800 flex justify-between items-center text-[10px] text-slate-500">
          <span>Fixed Geographic Compass: North (-Z) | South (+Z Solar Aperture)</span>
          <span>Parametric ISO 6946 Envelope Digital Twin</span>
        </div>
      </div>
    </div>
  );
}
