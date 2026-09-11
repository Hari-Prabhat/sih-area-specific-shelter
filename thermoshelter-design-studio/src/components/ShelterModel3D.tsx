import { useRef, useMemo, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Environment, ContactShadows, Float, Html, RoundedBox, Text } from '@react-three/drei';
import * as THREE from 'three';
import { ShelterDesign } from '../utils/thermalEngine';

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

/* ─── compass rose ─── */
function Compass({ orientation }: { orientation: number }) {
  const ref = useRef<THREE.Group>(null!);
  return (
    <group ref={ref} position={[0, 0.02, 0]} rotation={[0, -(orientation * Math.PI) / 180, 0]}>
      {/* N arrow */}
      <mesh position={[0, 0.01, -8]}>
        <coneGeometry args={[0.3, 0.8, 4]} />
        <meshStandardMaterial color="#ef4444" emissive="#ef4444" emissiveIntensity={0.3} />
      </mesh>
      <Text position={[0, 0.5, -9]} fontSize={0.5} color="#ef4444" anchorX="center" anchorY="middle">
        N
      </Text>
      {/* S */}
      <Text position={[0, 0.5, 9]} fontSize={0.4} color="#64748b" anchorX="center" anchorY="middle">
        S
      </Text>
      {/* E */}
      <Text position={[9, 0.5, 0]} fontSize={0.4} color="#64748b" anchorX="center" anchorY="middle">
        E
      </Text>
      {/* W */}
      <Text position={[-9, 0.5, 0]} fontSize={0.4} color="#64748b" anchorX="center" anchorY="middle">
        W
      </Text>
    </group>
  );
}

/* ─── window panel helper ─── */
function WindowPanel({ position, rotation, width, height }: {
  position: [number, number, number]; rotation: [number, number, number];
  width: number; height: number;
}) {
  return (
    <mesh position={position} rotation={rotation} castShadow>
      <planeGeometry args={[width, height]} />
      <meshPhysicalMaterial
        color="#88ccee"
        transparent
        opacity={0.4}
        roughness={0.05}
        metalness={0.1}
        transmission={0.7}
        thickness={0.05}
        side={THREE.DoubleSide}
      />
    </mesh>
  );
}

/* ─── door ─── */
function Door({ position, rotation }: {
  position: [number, number, number]; rotation: [number, number, number];
}) {
  return (
    <group position={position} rotation={rotation}>
      <mesh castShadow>
        <boxGeometry args={[1.0, 2.1, 0.08]} />
        <meshStandardMaterial color="#5a3825" roughness={0.7} />
      </mesh>
      {/* handle */}
      <mesh position={[0.35, 0, 0.06]}>
        <sphereGeometry args={[0.06, 16, 16]} />
        <meshStandardMaterial color="#d4a520" metalness={0.8} roughness={0.2} />
      </mesh>
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

/* ═══════════════════════════════════════════════════
   RECTANGULAR SHELTER
   ═══════════════════════════════════════════════════ */
function RectangularShelter({ design, wallColor, accentColor }: {
  design: ShelterDesign; wallColor: string; accentColor: string;
}) {
  const { length, width, height, roofAngle, wallThickness, windowArea, insulationType, thermalMassEnabled } = design;
  const roofRad = (roofAngle * Math.PI) / 180;
  const roofPeak = Math.tan(roofRad) * (width / 2);
  const roofHyp = (width / 2) / Math.cos(roofRad);

  // Dynamic window sizing from windowArea
  const numFrontWindows = 2;
  const singleWinArea = Math.max(0.2, (windowArea || 3) / numFrontWindows);
  const winW = Math.max(0.6, Math.min(2.4, Math.round(Math.sqrt(singleWinArea * 1.2) * 100) / 100));
  const winH = Math.max(0.6, Math.min(2.0, Math.round((singleWinArea / winW) * 100) / 100));

  const hasInsulation = Boolean(insulationType && insulationType !== 'None');

  return (
    <group>
      {/* ── walls ── */}
      {/* front */}
      <mesh position={[0, height / 2, width / 2]} castShadow receiveShadow>
        <boxGeometry args={[length, height, wallThickness]} />
        <meshStandardMaterial color={wallColor} roughness={0.8} />
      </mesh>
      {/* back */}
      <mesh position={[0, height / 2, -width / 2]} castShadow receiveShadow>
        <boxGeometry args={[length, height, wallThickness]} />
        <meshStandardMaterial color={wallColor} roughness={0.8} />
      </mesh>
      {/* left */}
      <mesh position={[-length / 2, height / 2, 0]} castShadow receiveShadow>
        <boxGeometry args={[wallThickness, height, width]} />
        <meshStandardMaterial color={wallColor} roughness={0.8} />
      </mesh>
      {/* right */}
      <mesh position={[length / 2, height / 2, 0]} castShadow receiveShadow>
        <boxGeometry args={[wallThickness, height, width]} />
        <meshStandardMaterial color={wallColor} roughness={0.8} />
      </mesh>

      {/* ── insulation envelope visual layer (yellow outline layer) ── */}
      {hasInsulation && (
        <mesh position={[0, height / 2, 0]}>
          <boxGeometry args={[length + 0.12, height + 0.05, width + 0.12]} />
          <meshStandardMaterial color="#eab308" transparent opacity={0.15} wireframe />
        </mesh>
      )}

      {/* ── pitched roof ── */}
      <mesh position={[0, height + roofPeak / 2, width / 4]}
        rotation={[roofRad, 0, 0]} castShadow>
        <boxGeometry args={[length + 0.4, roofHyp + 0.2, 0.12]} />
        <meshStandardMaterial color={accentColor} roughness={0.6} />
      </mesh>
      <mesh position={[0, height + roofPeak / 2, -width / 4]}
        rotation={[-roofRad, 0, 0]} castShadow>
        <boxGeometry args={[length + 0.4, roofHyp + 0.2, 0.12]} />
        <meshStandardMaterial color={accentColor} roughness={0.6} />
      </mesh>
      {/* ridge beam */}
      <mesh position={[0, height + roofPeak, 0]}>
        <boxGeometry args={[length + 0.5, 0.1, 0.1]} />
        <meshStandardMaterial color="#5a4a3a" roughness={0.6} />
      </mesh>

      {/* ── floor slab ── */}
      <mesh position={[0, 0.05, 0]} receiveShadow>
        <boxGeometry args={[length + 0.2, 0.1, width + 0.2]} />
        <meshStandardMaterial color="#4a4a48" roughness={0.9} />
      </mesh>

      {/* ── sensible thermal mass core slab ── */}
      {thermalMassEnabled && (
        <mesh position={[0, 0.11, 0]} receiveShadow>
          <boxGeometry args={[length * 0.8, 0.04, width * 0.8]} />
          <meshStandardMaterial color="#3b82f6" roughness={0.5} opacity={0.8} transparent />
        </mesh>
      )}

      {/* ── dynamic windows on front wall ── */}
      <WindowPanel position={[-length / 4, height / 2, width / 2 + 0.16]}
        rotation={[0, 0, 0]} width={winW} height={winH} />
      <WindowPanel position={[length / 4, height / 2, width / 2 + 0.16]}
        rotation={[0, 0, 0]} width={winW} height={winH} />

      {/* ── window on back wall ── */}
      <WindowPanel position={[0, height / 2, -(width / 2 + 0.16)]}
        rotation={[0, Math.PI, 0]} width={winW * 0.8} height={winH * 0.8} />

      {/* ── door on front ── */}
      <Door position={[0, 1.05, width / 2 + 0.06]} rotation={[0, 0, 0]} />

      {/* ── dimension labels ── */}
      <DimensionLabel start={[-length / 2, 0, width / 2 + 1.5]} end={[length / 2, 0, width / 2 + 1.5]}
        label={`${length}m`} offset={0.3} />
      <DimensionLabel start={[length / 2 + 1.5, 0, -width / 2]} end={[length / 2 + 1.5, 0, width / 2]}
        label={`${width}m`} offset={0.3} />
      <DimensionLabel start={[length / 2 + 1, 0, width / 2]} end={[length / 2 + 1, height, width / 2]}
        label={`${height}m`} offset={0} />
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
      {/* flat roof */}
      <mesh position={[0, h, 0]} castShadow>
        <cylinderGeometry args={[r + 0.15, r + 0.15, 0.15, 48]} />
        <meshStandardMaterial color={accentColor} roughness={0.6} />
      </mesh>
      {/* floor */}
      <mesh position={[0, 0.05, 0]} receiveShadow>
        <cylinderGeometry args={[r + 0.1, r + 0.1, 0.1, 48]} />
        <meshStandardMaterial color="#4a4a48" roughness={0.9} />
      </mesh>
      {/* windows */}
      <WindowPanel position={[0, h / 2, r + 0.05]} rotation={[0, 0, 0]} width={1.2} height={1.0} />
      <WindowPanel position={[r + 0.05, h / 2, 0]} rotation={[0, Math.PI / 2, 0]} width={1.2} height={1.0} />
      {/* door */}
      <Door position={[0, 1.05, r + 0.05]} rotation={[0, 0, 0]} />
      {/* labels */}
      <DimensionLabel start={[0, 0, 0]} end={[r, 0, 0]} label={`R=${r.toFixed(1)}m`} offset={0.3} />
      <DimensionLabel start={[r + 1, 0, 0]} end={[r + 1, h, 0]} label={`${h}m`} offset={0} />
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
      <Door position={[0, 1.05, r - 0.05]} rotation={[0, 0, 0]} />
      {/* windows */}
      <WindowPanel position={[r * 0.7, r * 0.5, r * 0.7]} rotation={[0, Math.PI / 4, 0]} width={0.9} height={0.7} />
      <WindowPanel position={[-r * 0.7, r * 0.5, r * 0.7]} rotation={[0, -Math.PI / 4, 0]} width={0.9} height={0.7} />
      {/* labels */}
      <DimensionLabel start={[0, 0, 0]} end={[r, 0, 0]} label={`R=${r.toFixed(1)}m`} offset={0.3} />
      <DimensionLabel start={[r + 1, 0, 0]} end={[r + 1, r, 0]} label={`${h}m`} offset={0} />
    </group>
  );
}

/* ═══════════════════════════════════════════════════
   PYRAMID SHELTER
   ═══════════════════════════════════════════════════ */
function PyramidShelter({ design, wallColor, accentColor }: {
  design: ShelterDesign; wallColor: string; accentColor: string;
}) {
  const { length, width, height } = design;

  /* Build a simple truncated pyramid using a custom geometry */
  const vertices = useMemo(() => {
    const topScale = 0.15;
    const tl = length * topScale;
    const tw = width * topScale;
    return new Float32Array([
      // base quad (two triangles)
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
      {/* edge accent */}
      <mesh geometry={geometry}>
        <meshStandardMaterial color={accentColor} transparent opacity={0.15} wireframe side={THREE.DoubleSide} />
      </mesh>
      {/* floor */}
      <mesh position={[0, 0.05, 0]} receiveShadow>
        <boxGeometry args={[length + 0.2, 0.1, width + 0.2]} />
        <meshStandardMaterial color="#4a4a48" roughness={0.9} />
      </mesh>
      {/* door */}
      <Door position={[0, 1.05, width / 2 + 0.06]} rotation={[0, 0, 0]} />
      {/* labels */}
      <DimensionLabel start={[-length / 2, 0, width / 2 + 1.5]} end={[length / 2, 0, width / 2 + 1.5]}
        label={`${length}m`} offset={0.3} />
      <DimensionLabel start={[length / 2 + 1.5, 0, -width / 2]} end={[length / 2 + 1.5, 0, width / 2]}
        label={`${width}m`} offset={0.3} />
      <DimensionLabel start={[length / 2 + 1, 0, width / 2]} end={[length / 2 + 1, height, width / 2]}
        label={`${height}m`} offset={0} />
    </group>
  );
}

/* ─── animated sun ─── */
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

/* ═══════════════════════════════════════════════════
   MAIN 3D SCENE
   ═══════════════════════════════════════════════════ */
function ShelterScene({ design, materialName, comfortIndex, avgTemp }: {
  design: ShelterDesign; materialName: string; comfortIndex?: number; avgTemp?: number;
}) {
  const colors = getColors(materialName);
  const groupRef = useRef<THREE.Group>(null!);

  /* Slow gentle auto-rotation */
  useFrame(({ clock }) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = Math.sin(clock.getElapsedTime() * 0.05) * 0.15;
    }
  });

  const shelterProps = { design, wallColor: colors.wall, accentColor: colors.accent };

  return (
    <>
      <ambientLight intensity={0.35} />
      <SunLight />
      <pointLight position={[-8, 8, -8]} intensity={0.4} color="#b0c4de" />
      {comfortIndex !== undefined && <ThermalGlow comfortIndex={comfortIndex} />}

      <group ref={groupRef}>
        <Compass orientation={design.orientation} />
        <GroundGrid />

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
        maxPolarAngle={Math.PI / 2.1}
        minDistance={5}
        maxDistance={30}
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
              Interactive
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-slate-500">Drag to rotate • Scroll to zoom</span>
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="text-[10px] px-2 py-1 bg-slate-700/50 text-slate-400 rounded hover:bg-slate-600/50 hover:text-white transition"
            >
              {isFullscreen ? '✕ Close' : '⛶ Fullscreen'}
            </button>
          </div>
        </div>

        {/* canvas */}
        <div className={isFullscreen ? 'h-[calc(100%-40px)]' : 'h-[420px]'}>
          <Canvas
            camera={{ position: cameraPos, fov: 45 }}
            shadows
            dpr={[1, 2]}
            gl={{ antialias: true, alpha: false }}
            onCreated={({ gl }) => {
              gl.toneMapping = THREE.ACESFilmicToneMapping;
              gl.toneMappingExposure = 1.2;
            }}
          >
            <ShelterScene
              design={design}
              materialName={materialName}
              comfortIndex={comfortIndex}
              avgTemp={avgTemp}
            />
          </Canvas>
        </div>
      </div>
    </div>
  );
}
