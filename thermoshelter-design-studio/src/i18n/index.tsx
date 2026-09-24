/**
 * THERMOSHELTER — Internationalization (product-hardening pass)
 * =============================================================
 * Scalable locale architecture: translations live in LOCALES (one namespace
 * per language), components consume `t(key)` through the LocaleProvider.
 * English is the default and the source of truth; other locales override it
 * key-by-key. Numbers/units (°C, kWh, m², W/m²K) are never translated.
 */
import { createContext, useCallback, useContext, useMemo, useState, ReactNode } from 'react';

export type Locale = 'en' | 'hi' | 'te' | 'ta' | 'kn' | 'bn' | 'mr';

export const LOCALE_LIST: { code: Locale; nativeLabel: string }[] = [
  { code: 'en', nativeLabel: 'English' },
  { code: 'hi', nativeLabel: 'हिन्दी' },
  { code: 'te', nativeLabel: 'తెలుగు' },
  { code: 'ta', nativeLabel: 'தமிழ்' },
  { code: 'kn', nativeLabel: 'ಕನ್ನಡ' },
  { code: 'bn', nativeLabel: 'বাংলা' },
  { code: 'mr', nativeLabel: 'मराठी' },
];

const STORAGE_KEY = 'thermoshelter.locale';

/**
 * Translation keys. English values double as fallbacks for any key a
 * partial locale has not overridden yet — no component ever shows a raw key.
 */
const en = {
  // Landing
  landingTagline: 'Area-Specific Passive Shelter Digital Twin & Thermal Optimizer',
  landingIntro:
    'ThermoShelter is an engineering platform for designing and evaluating area-specific shelters for thermal comfort across extreme and diverse climates.',
  landingDetail:
    'From local climate and shelter geometry to thermal simulation, optimization, engineering blueprint and 3D digital twin — ThermoShelter connects the complete design workflow in one system.',
  enterStudio: 'Enter Design Studio',
  howItWorks: 'How It Works',
  theChallenge: 'The Challenge',
  challengeBody:
    'Shelter performance changes significantly with climate, geometry, orientation, envelope materials, insulation, openings, thermal mass and passive design strategy. ThermoShelter evaluates these factors together to support area-specific shelter design.',
  workflow: 'Workflow',
  capabilities: 'Capabilities',
  capClimateTitle: 'Area-Specific Climate',
  capClimateBody: 'Resolve location and climate data for the selected site.',
  capSimTitle: 'Thermal Simulation',
  capSimBody: 'Predict shelter temperature and heat flow using the Python thermal engine.',
  capPassiveTitle: 'Passive Design',
  capPassiveBody: 'Evaluate insulation, orientation, openings, thermal mass and passive strategies.',
  capOptTitle: 'Optimization',
  capOptBody: 'Search feasible configurations for improved simulated thermal comfort.',
  capBlueprintTitle: 'Engineering Blueprint',
  capBlueprintBody: 'Generate dimensions, materials, orientation and thermal annotations.',
  capTwinTitle: '3D Digital Twin',
  capTwinBody: 'Visualize the same canonical shelter design in 3D.',
  honestyNote:
    'ThermoShelter uses a reduced-order thermal simulation model for rapid design exploration. High-fidelity tools such as ANSYS are not currently integrated into the prototype.',
  // Landing — How It Works pipeline
  howClimate: 'Resolve the site location and its climate profile with honest data provenance.',
  howMission: 'Capture occupancy, mission duration and shelter requirements.',
  howDesign: 'Configure geometry, shape, envelope materials, openings and orientation.',
  howSimulation: 'Run the Python thermal engine over a 168-hour horizon.',
  howOptimization: 'Search feasible designs and compare against a comfort-first recommendation.',
  howBlueprint: 'Generate dimensioned drawings with thermal annotations.',
  howReport: 'Assemble a structured engineering report, ready to paste into a document.',
  // Landing — Design → Analysis → Decision
  designDecisionTitle: 'Design → Analysis → Decision',
  designStage: 'Design',
  designStageBody: 'Geometry, shape, materials, insulation, openings and orientation.',
  analysisStage: 'Analysis',
  analysisStageBody: 'Temperature, heat flow, solar gain and simulated comfort.',
  decisionStage: 'Decision',
  decisionStageBody: 'Your requirement-constrained design versus the ThermoShelter comfort-first recommendation.',
  // Landing — climates + outputs
  extremeClimatesTitle: 'Built for Extreme Climates',
  climColdTitle: 'Cold / High Altitude',
  climColdBody: 'Leh / Ladakh — solar capture and high-performance envelope.',
  climHotDryTitle: 'Hot-Dry',
  climHotDryBody: 'Jaisalmer — thermal mass and nocturnal ventilation.',
  climHumidTitle: 'Warm-Humid',
  climHumidBody: 'Coastal and southern regions — shading and airflow.',
  climCompositeTitle: 'Composite / Mixed',
  climCompositeBody: 'Indian plains — seasonal passive strategies.',
  climatesDisclaimer: 'Representative examples — the climate resolver supports locations across India.',
  outputsTitle: 'What ThermoShelter Generates',
  outThermalTitle: 'Thermal Results',
  outThermalBody: 'Temperature, comfort hours, heat flow and solar energy.',
  outOptimizedTitle: 'Optimized Design',
  outOptimizedBody: 'User-constrained results plus a comfort-first recommendation.',
  outBlueprintTitle: 'Engineering Blueprint',
  outBlueprintBody: 'Dimensions, materials and thermal annotations.',
  outTwinTitle: '3D Digital Twin',
  outTwinBody: 'Parametric shelter visualization of the canonical design.',
  // Shell / navigation
  appSubtitle: 'Area-Specific Passive Shelter Digital Twin & Thermal Design Optimization',
  stageClimate: 'Site & Climate',
  stageMission: 'Mission',
  stageDesign: 'Design',
  stagePassive: 'Passive Strategy',
  stageSimulation: 'Simulation',
  stageOptimization: 'Optimization',
  stageBlueprint: 'Blueprint',
  stageTwin: '3D Twin',
  stageReport: 'Report',
  back: 'Back',
  next: 'Next',
  themeDark: 'Dark theme',
  themeLight: 'Light theme',
  language: 'Language',
  currentDesign: 'Current Design',
  noDesignYet: 'No design configured yet',
  // Workflow actions
  runSimulation: 'Run Simulation',
  runOptimization: 'Optimize Design',
  applyCandidate: 'Apply Candidate',
  applyRecommendation: 'Apply Recommendation',
  yourDesign: 'Your Design — User Requirements',
  recommendedDesign: 'ThermoShelter Recommended Design — Comfort First',
  whyRecommends: 'Why ThermoShelter recommends this design',
  copyReport: 'Copy Report',
  reportCopied: 'Report copied — ready to paste into Word or Google Docs.',
  // Empty / honest states
  noSimulationResults: 'No Simulation Results Yet',
  noOptimizationResults: 'No Optimization Results Yet',
  footer: 'ThermoShelter Design Studio | SIH 2026 | SIH26051 | DRDO - Problem Statement',
};

export type TranslationKey = keyof typeof en;

const hi: Partial<Record<TranslationKey, string>> = {
  landingTagline: 'क्षेत्र-विशिष्ट पैसिव आश्रय डिजिटल ट्विन एवं थर्मल ऑप्टिमाइज़र',
  landingIntro:
    'ThermoShelter चरम और विविध जलवायुओं में तापीय आराम के लिए क्षेत्र-विशिष्ट आश्रयों के डिज़ाइन और मूल्यांकन हेतु एक इंजीनियरिंग प्लेटफ़ॉर्म है।',
  landingDetail:
    'स्थानीय जलवायु और आश्रय ज्यामिति से लेकर थर्मल सिमुलेशन, अनुकूलन, इंजीनियरिंग ब्लूप्रिंट और 3D डिजिटल ट्विन तक — ThermoShelter संपूर्ण डिज़ाइन कार्यप्रवाह को एक प्रणाली में जोड़ता है।',
  enterStudio: 'डिज़ाइन स्टूडियो खोलें',
  howItWorks: 'यह कैसे कार्य करता है',
  theChallenge: 'चुनौती',
  challengeBody:
    'आश्रय का प्रदर्शन जलवायु, ज्यामिति, अभिविन्यास, खोल (envelope) सामग्री, इन्सुलेशन, खिड़की-दरवाज़े, थर्मल मास और पैसिव रणनीति के साथ बदलता है। ThermoShelter क्षेत्र-विशिष्ट आश्रय डिज़ाइन हेतु इन सबका साथ मूल्यांकन करता है।',
  workflow: 'कार्यप्रवाह',
  capabilities: 'क्षमताएँ',
  capClimateTitle: 'क्षेत्र-विशिष्ट जलवायु',
  capClimateBody: 'चयनित स्थल के लिए स्थान एवं जलवायु डेटा प्राप्त करें।',
  capSimTitle: 'थर्मल सिमुलेशन',
  capSimBody: 'Python थर्मल इंजन से आश्रय के तापमान एवं ऊष्मा प्रवाह का अनुमान।',
  capPassiveTitle: 'पैसिव डिज़ाइन',
  capPassiveBody: 'इन्सुलेशन, अभिविन्यास, खुले भाग, थर्मल मास एवं पैसिव रणनीतियों का मूल्यांकन।',
  capOptTitle: 'अनुकूलन',
  capOptBody: 'बेहतर अनुकरित तापीय आराम हेतु संभव विन्यासों की खोज।',
  capBlueprintTitle: 'इंजीनियरिंग ब्लूप्रिंट',
  capBlueprintBody: 'विमाएँ, सामग्री, अभिविन्यास एवं तापीय एनोटेशन तैयार करें।',
  capTwinTitle: '3D डिजिटल ट्विन',
  capTwinBody: 'उसी canonical आश्रय डिज़ाइन को 3D में देखें।',
  appSubtitle: 'क्षेत्र-विशिष्ट पैसिव आश्रय डिजिटल ट्विन एवं थर्मल डिज़ाइन अनुकूलन',
  stageClimate: 'स्थल एवं जलवायु',
  stageMission: 'मिशन',
  stageDesign: 'डिज़ाइन',
  stagePassive: 'पैसिव रणनीति',
  stageSimulation: 'सिमुलेशन',
  stageOptimization: 'अनुकूलन',
  stageBlueprint: 'ब्लूप्रिंट',
  stageTwin: '3D ट्विन',
  stageReport: 'रिपोर्ट',
  back: 'वापस',
  next: 'आगे',
  themeDark: 'गहरी थीम',
  themeLight: 'हल्की थीम',
  language: 'भाषा',
  currentDesign: 'वर्तमान डिज़ाइन',
  noDesignYet: 'अभी कोई डिज़ाइन कॉन्फ़िगर नहीं हुआ',
  runSimulation: 'सिमुलेशन चलाएँ',
  runOptimization: 'डिज़ाइन अनुकूलित करें',
  applyCandidate: 'उम्मीदवार लागू करें',
  applyRecommendation: 'अनुशंसा लागू करें',
  yourDesign: 'आपका डिज़ाइन — उपयोगकर्ता आवश्यकताएँ',
  recommendedDesign: 'ThermoShelter अनुशंसित डिज़ाइन — आराम प्रथम',
  whyRecommends: 'ThermoShelter यह डिज़ाइन क्यों अनुशंसित करता है',
  copyReport: 'रिपोर्ट कॉपी करें',
  reportCopied: 'रिपोर्ट कॉपी हो गई — Word या Google Docs में पेस्ट करें।',
  noSimulationResults: 'अभी कोई सिमुलेशन परिणाम नहीं',
  noOptimizationResults: 'अभी कोई अनुकूलन परिणाम नहीं',
  designDecisionTitle: 'डिज़ाइन → विश्लेषण → निर्णय',
  designStage: 'डिज़ाइन',
  designStageBody: 'ज्यामिति, आकार, सामग्री, इन्सुलेशन, खुले भाग और अभिविन्यास।',
  analysisStage: 'विश्लेषण',
  analysisStageBody: 'तापमान, ऊष्मा प्रवाह, सौर लाभ और अनुकरित आराम।',
  decisionStage: 'निर्णय',
  decisionStageBody: 'आपका आवश्यकता-बद्ध डिज़ाइन बनाम ThermoShelter आराम-प्रथम अनुशंसा।',
  extremeClimatesTitle: 'चरम जलवायु के लिए निर्मित',
  climatesDisclaimer: 'प्रतिनिधि उदाहरण — जलवायु रिज़ॉल्वर भारत भर के स्थानों का समर्थन करता है।',
  outputsTitle: 'ThermoShelter क्या तैयार करता है',
};

const te: Partial<Record<TranslationKey, string>> = {
  landingTagline: 'ప్రాంత-నిర్దిష్ట పాసివ్ షెల్టర్ డిజిటల్ ట్విన్ & థర్మల్ ఆప్టిమైజర్',
  landingIntro:
    'తీవ్రమైన, వైవిధ్యమైన వాతావరణాల్లో ఉష్ణ సౌకర్యం కోసం ప్రాంత-నిర్దిష్ట షెల్టర్ల రూపకల్పన మరియు మూల్యాంకనం కోసం ThermoShelter ఒక ఇంజనీరింగ్ వేదిక.',
  landingDetail:
    'స్థానిక వాతావరణం మరియు షెల్టర్ జ్యామెట్రీ నుండి థర్మల్ సిమ్యులేషన్, ఆప్టిమైజేషన్, ఇంజనీరింగ్ బ్లూప్రింట్ మరియు 3D డిజిటల్ ట్విన్ వరకు — పూర్తి డిజైన్ ప్రవాహాన్ని ఒకే వ్యవస్థలో అనుసంధానిస్తుంది.',
  enterStudio: 'డిజైన్ స్టూడియోని ప్రారంభించండి',
  howItWorks: 'ఇది ఎలా పనిచేస్తుంది',
  theChallenge: 'సవాలు',
  challengeBody:
    'వాతావరణం, జ్యామెట్రీ, దిశ, ఎన్వలప్ పదార్థాలు, ఇన్సులేషన్, తెరిచీకట్లు, థర్మల్ మాస్ మరియు పాసివ్ వ్యూహాలతో షెల్టర్ పనితీయు గణనీయంగా మారుతుంది. ThermoShelter ప్రాంత-నిర్దిష్ట షెల్టర్ రూపకల్పన కోసం వీటన్నింటినీ కలిపి మూల్యాంకనం చేస్తుంది.',
  workflow: 'కార్యప్రవాహం',
  capabilities: 'సామర్థ్యాలు',
  capClimateTitle: 'ప్రాంత-నిర్దిష్ట వాతావరణం',
  capClimateBody: 'ఎంచుకున్న ప్రదేశం కోసం స్థానం మరియు వాతావరణ డేటాను పొందండి.',
  capSimTitle: 'థర్మల్ సిమ్యులేషన్',
  capSimBody: 'Python థర్మల్ ఇంజన్‌తో షెల్టర్ ఉష్ణోగ్రత మరియు ఉష్ణ ప్రవాహాన్ని అంచనా వేయండి.',
  capPassiveTitle: 'పాసివ్ డిజైన్',
  capPassiveBody: 'ఇన్సులేషన్, దిశ, తెరవాట్లు, థర్మల్ మాస్ మరియు పాసివ్ వ్యూహాలను మూల్యాంకనం చేయండి.',
  capOptTitle: 'ఆప్టిమైజేషన్',
  capOptBody: 'మెరుగైన అనుకరించిన ఉష్ణ సౌకర్యం కోసం సాధ్యమయ్యే కాన్ఫిగరేషన్లను వెతకండి.',
  capBlueprintTitle: 'ఇంజనీరింగ్ బ్లూప్రింట్',
  capBlueprintBody: 'కొలతలు, పదార్థాలు, దిశ మరియు థర్మల్ ఏనోటేషన్లను సృష్టించండి.',
  capTwinTitle: '3D డిజిటల్ ట్విన్',
  capTwinBody: 'అదే కానానికల్ షెల్టర్ డిజైన్‌ను 3D లో విజువలైజ్ చేయండి.',
  appSubtitle: 'ప్రాంత-నిర్దిష్ట పాసివ్ షెల్టర్ డిజిటల్ ట్విన్ & థర్మల్ డిజైన్ ఆప్టిమైజేషన్',
  stageClimate: 'స్థలం & వాతావరణం',
  stageMission: 'మిషన్',
  stageDesign: 'డిజైన్',
  stagePassive: 'పాసివ్ వ్యూహం',
  stageSimulation: 'సిమ్యులేషన్',
  stageOptimization: 'ఆప్టిమైజేషన్',
  stageBlueprint: 'బ్లూప్రింట్',
  stageTwin: '3D ట్విన్',
  stageReport: 'నివేదిక',
  back: 'వెనుకకు',
  next: 'తర్వాత',
  themeDark: 'డార్క్ థీమ్',
  themeLight: 'లైట్ థీమ్',
  language: 'భాష',
  currentDesign: 'ప్రస్తుత డిజైన్',
  noDesignYet: 'ఇంకా డిజైన్ కాన్ఫిగర్ చేయలేదు',
  runSimulation: 'సిమ్యులేషన్ రన్ చేయండి',
  runOptimization: 'డిజైన్‌ను ఆప్టిమైజ్ చేయండి',
  applyCandidate: 'కాండిడేట్‌ను వర్తింపు చేయండి',
  applyRecommendation: 'సిఫారసును వర్తింపు చేయండి',
  yourDesign: 'మీ డిజైన్ — యూజర్ అవసరాలు',
  recommendedDesign: 'ThermoShelter సిఫారసు చేసిన డిజైన్ — కంఫర్ట్ ఫస్ట్',
  whyRecommends: 'ThermoShelter ఈ డిజైన్‌ను ఎందుకు సిఫారసు చేస్తుంది',
  copyReport: 'నివేదికను కాపీ చేయండి',
  reportCopied: 'నివేదిక కాపీ అయింది — Word లేదా Google Docs లో పేస్ట్ చేయండి.',
  noSimulationResults: 'ఇంకా సిమ్యులేషన్ ఫలితాలు లేవు',
  noOptimizationResults: 'ఇంకా ఆప్టిమైజేషన్ ఫలితాలు లేవు',
  designDecisionTitle: 'డిజైన్ → విశ్లేషణ → నిర్ణయం',
  designStage: 'డిజైన్',
  designStageBody: 'జ్యామెట్రీ, ఆకారం, పదార్థాలు, ఇన్సులేషన్, తెరవాట్లు మరియు దిశ.',
  analysisStage: 'విశ్లేషణ',
  analysisStageBody: 'ఉష్ణోగ్రత, ఉష్ణ ప్రవాహం, సౌర లాభం మరియు అనుకరించిన సౌకర్యం.',
  decisionStage: 'నిర్ణయం',
  decisionStageBody: 'మీ అవసరాల-బద్ధ డిజైన్ vs ThermoShelter కంఫర్ట్-ఫస్ట్ సిఫారసు.',
  extremeClimatesTitle: 'తీవ్ర వాతావరణాల కోసం నిర్మించబడింది',
  climatesDisclaimer: 'ప్రాతినిధ్య ఉదాహరణలు — క్లైమేట్ రిజాల్వర్ భారతవ్యాప్తంగా స్థలాలకు మద్దతు ఇస్తుంది.',
  outputsTitle: 'ThermoShelter ఏమి సృష్టిస్తుంది',
};

const ta: Partial<Record<TranslationKey, string>> = {
  landingTagline: 'பகுதி-சார்ந்த பாசிவ் அடைக்கல டிஜிட்டல் டிவின் & வெப்ப மேம்படுத்தி',
  landingIntro:
    'கடுமையான மற்றும் பல்வேறு காலநிலைகளில் வெப்ப ஆறுதலுக்கான பகுதி-சார்ந்த அடைக்கலங்களை வடிவமைக்கவும் மதிப்பிடவும் ThermoShelter ஒரு பொறியியல் தளம்.',
  enterStudio: 'டிசைன் ஸ்டூடியோவைத் திறக்கவும்',
  theChallenge: 'சவால்',
  workflow: 'பணிப்பாட்டம்',
  capabilities: 'திறன்கள்',
  appSubtitle: 'பகுதி-சார்ந்த பாசிவ் அடைக்கல டிஜிட்டல் டிவின் & வெப்ப வடிவமைப்பு மேம்பாடு',
  stageClimate: 'இடம் & காலநிலை',
  stageMission: 'பணி',
  stageDesign: 'வடிவமைப்பு',
  stagePassive: 'பாசிவ் உத்தி',
  stageSimulation: 'ஒப்புருவாக்கம்',
  stageOptimization: 'மேம்பாடு',
  stageBlueprint: 'நீலச்சித்திரம்',
  stageTwin: '3D டிவின்',
  stageReport: 'அறிக்கை',
  back: 'பின்செல்',
  next: 'அடுத்து',
  themeDark: 'இருள் தீம்',
  themeLight: 'ஒளி தீம்',
  language: 'மொழி',
  currentDesign: 'தற்போதைய வடிவமைப்பு',
  runSimulation: 'ஒப்புருவாக்கம் இயக்கு',
  runOptimization: 'வடிவமைப்பை மேம்படுத்து',
  applyCandidate: 'வேட்பாளரைப் பயன்படுத்து',
  applyRecommendation: 'பரிந்துரையைப் பயன்படுத்து',
  copyReport: 'அறிக்கையை நகலெடு',
  noSimulationResults: 'இன்னும் ஒப்புரு முடிவுகள் இல்லை',
};

const kn: Partial<Record<TranslationKey, string>> = {
  landingTagline: 'ಪ್ರದೇಶ-ನಿರ್ದಿಷ್ಟ ಪ್ಯಾಸಿವ್ ಆಶ್ರಯ ಡಿಜಿಟಲ್ ಟ್ವಿನ್ & ಥರ್ಮಲ್ ಆಪ್ಟಿಮೈಜರ್',
  landingIntro:
    'ತೀವ್ರ ಮತ್ತು ವೈವಿಧ್ಯಮಯ ಹವಾಮಾನಗಳಲ್ಲಿ ಉಷ್ಣ ಆರಾಮಕ್ಕಾಗಿ ಪ್ರದೇಶ-ನಿರ್ದಿಷ್ಟ ಆಶ್ರಯಗಳ ವಿನ್ಯಾಸ ಮತ್ತು ಮೌಲ್ಯಮಾಪನಕ್ಕಾಗಿ ThermoShelter ಒಂದು ಎಂಜಿನಿಯರಿಂಗ್ ವೇದಿಕೆ.',
  enterStudio: 'ಡಿಸೈನ್ ಸ್ಟುಡಿಯೊ ತೆರೆಯಿರಿ',
  theChallenge: 'ಸವಾಲು',
  workflow: 'ಕಾರ್ಯಪ್ರವಾಹ',
  capabilities: 'ಸಾಮರ್ಥ್ಯಗಳು',
  appSubtitle: 'ಪ್ರದೇಶ-ನಿರ್ದಿಷ್ಟ ಪ್ಯಾಸಿವ್ ಆಶ್ರಯ ಡಿಜಿಟಲ್ ಟ್ವಿನ್ & ಥರ್ಮಲ್ ಡಿಸೈನ್ ಆಪ್ಟಿಮೈಸೇಶನ್',
  stageClimate: 'ಸ್ಥಳ & ಹವಾಮಾನ',
  stageMission: 'ಮಿಷನ್',
  stageDesign: 'ಡಿಸೈನ್',
  stagePassive: 'ಪ್ಯಾಸಿವ್ ತಂತ್ರ',
  stageSimulation: 'ಸಿಮ್ಯುಲೇಶನ್',
  stageOptimization: 'ಆಪ್ಟಿಮೈಸೇಶನ್',
  stageBlueprint: 'ಬ್ಲೂಪ್ರಿಂಟ್',
  stageTwin: '3D ಟ್ವಿನ್',
  stageReport: 'ವರದಿ',
  back: 'ಹಿಂದೆ',
  next: 'ಮುಂದೆ',
  themeDark: 'ಡಾರ್ಕ್ ಥೀಮ್',
  themeLight: 'ಲೈಟ್ ಥೀಮ್',
  language: 'ಭಾಷೆ',
  currentDesign: 'ಪ್ರಸ್ತುತ ಡಿಸೈನ್',
  runSimulation: 'ಸಿಮ್ಯುಲೇಶನ್ ರನ್ ಮಾಡಿ',
  runOptimization: 'ಡಿಸೈನ್ ಆಪ್ಟಿಮೈಸ್ ಮಾಡಿ',
  applyCandidate: 'ಅಭ್ಯರ್ಥಿಯನ್ನು ಅನ್ವಯಿಸಿ',
  applyRecommendation: 'ಶಿಫಾರಸನ್ನು ಅನ್ವಯಿಸಿ',
  copyReport: 'ವರದಿಯನ್ನು ನಕಲಿಸಿ',
  noSimulationResults: 'ಇನ್ನೂ ಸಿಮ್ಯುಲೇಶನ್ ಫಲಿತಾಂಶಗಳಿಲ್ಲ',
};

const bn: Partial<Record<TranslationKey, string>> = {
  landingTagline: 'অঞ্চল-নির্দিষ্ট প্যাসিভ আশ্রয় ডিজিটাল টুইন ও থার্মাল অপ্টিমাইজার',
  landingIntro:
    'চরম ও বৈচিত্র্যময় জলবায়ুতে তাপীয় আরামের জন্য অঞ্চল-নির্দিষ্ট আশ্রয়ের নকশা ও মূল্যায়নের জন্য ThermoShelter একটি প্রকৌশল প্ল্যাটফর্ম।',
  enterStudio: 'ডিজাইন স্টুডিও খুলুন',
  theChallenge: 'চ্যালেঞ্জ',
  workflow: 'কর্মপ্রবাহ',
  capabilities: 'সক্ষমতা',
  appSubtitle: 'অঞ্চল-নির্দিষ্ট প্যাসিভ আশ্রয় ডিজিটাল টুইন ও থার্মাল ডিজাইন অপ্টিমাইজেশন',
  stageClimate: 'স্থান ও জলবায়ু',
  stageMission: 'মিশন',
  stageDesign: 'ডিজাইন',
  stagePassive: 'প্যাসিভ কৌশল',
  stageSimulation: 'সিমুলেশন',
  stageOptimization: 'অপ্টিমাইজেশন',
  stageBlueprint: 'নীলনকশা',
  stageTwin: '3D টুইন',
  stageReport: 'প্রতিবেদন',
  back: 'পিছনে',
  next: 'পরবর্তী',
  themeDark: 'ডার্ক থিম',
  themeLight: 'লাইট থিম',
  language: 'ভাষা',
  currentDesign: 'বর্তমান ডিজাইন',
  runSimulation: 'সিমুলেশন চালান',
  runOptimization: 'ডিজাইন অপ্টিমাইজ করুন',
  applyCandidate: 'প্রার্থী প্রয়োগ করুন',
  applyRecommendation: 'সুপারিশ প্রয়োগ করুন',
  copyReport: 'প্রতিবেদন কপি করুন',
  noSimulationResults: 'এখনও সিমুলেশন ফলাফল নেই',
};

const mr: Partial<Record<TranslationKey, string>> = {
  landingTagline: 'क्षेत्र-विशिष्ट पॅसिव्ह आश्रय डिजिटल ट्विन आणि थर्मल ऑप्टिमायझर',
  landingIntro:
    'अत्यंत आणि विविध हवामानात उष्णता आरामासाठी क्षेत्र-विशिष्ट आश्रयांच्या डिझाइन आणि मूल्यमापनासाठी ThermoShelter एक अभियांत्रिकी व्यासपीठ आहे.',
  enterStudio: 'डिझाइन स्टुडिओ उघडा',
  theChallenge: 'आव्हान',
  workflow: 'कार्यप्रवाह',
  capabilities: 'क्षमता',
  appSubtitle: 'क्षेत्र-विशिष्ट पॅसिव्ह आश्रय डिजिटल ट्विन आणि थर्मल डिझाइन ऑप्टिमायझेशन',
  stageClimate: 'स्थळ आणि हवामान',
  stageMission: 'मिशन',
  stageDesign: 'डिझाइन',
  stagePassive: 'पॅसिव्ह धोरण',
  stageSimulation: 'सिम्युलेशन',
  stageOptimization: 'ऑप्टिमायझेशन',
  stageBlueprint: 'निळी नकाशा',
  stageTwin: '3D ट्विन',
  stageReport: 'अहवाल',
  back: 'मागे',
  next: 'पुढे',
  themeDark: 'डार्क थीम',
  themeLight: 'लाइट थीम',
  language: 'भाषा',
  currentDesign: 'सध्याची डिझाइन',
  runSimulation: 'सिम्युलेशन चालवा',
  runOptimization: 'डिझाइन ऑप्टिमाइझ करा',
  applyCandidate: 'उमेदवार लागू करा',
  applyRecommendation: 'शिफारस लागू करा',
  copyReport: 'अहवाल कॉपी करा',
  noSimulationResults: 'अजून सिम्युलेशन निकाल नाहीत',
};

const LOCALES: Record<Locale, Partial<Record<TranslationKey, string>>> = {
  en: {},
  hi,
  te,
  ta,
  kn,
  bn,
  mr,
};

interface LocaleContextValue {
  locale: Locale;
  setLocale: (l: Locale) => void;
  /** Translate a key; falls back to the English source string. */
  t: (key: TranslationKey) => string;
}

const LocaleContext = createContext<LocaleContextValue | null>(null);

function readStoredLocale(): Locale {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored && stored in LOCALES) return stored as Locale;
  } catch {
    /* localStorage unavailable (private mode) — default to English */
  }
  return 'en';
}

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(readStoredLocale);

  const setLocale = useCallback((l: Locale) => {
    setLocaleState(l);
    try {
      localStorage.setItem(STORAGE_KEY, l);
    } catch {
      /* persistence unavailable — session-scoped selection */
    }
    // Keep the document language attribute correct for screen readers.
    document.documentElement.lang = l;
  }, []);

  const t = useCallback(
    (key: TranslationKey) => LOCALES[locale]?.[key] ?? en[key],
    [locale],
  );

  const value = useMemo(() => ({ locale, setLocale, t }), [locale, setLocale, t]);
  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}

export function useLocale(): LocaleContextValue {
  const ctx = useContext(LocaleContext);
  if (!ctx) throw new Error('useLocale must be used inside LocaleProvider');
  return ctx;
}

/** Language selector: compact, accessible, keyboard-operable. */
export function LanguageSelector() {
  const { locale, setLocale, t } = useLocale();
  return (
    <label className="flex items-center gap-1.5 text-xs text-[var(--text-secondary)]">
      <span className="sr-only">{t('language')}</span>
      <span aria-hidden="true" className="opacity-70">🌐</span>
      <select
        value={locale}
        onChange={(e) => setLocale(e.target.value as Locale)}
        aria-label={t('language')}
        className="bg-[var(--surface-elevated)] border border-[var(--border)] rounded-md px-1.5 py-1 text-xs text-[var(--text-primary)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent-primary)]"
      >
        {LOCALE_LIST.map((l) => (
          <option key={l.code} value={l.code}>
            {l.nativeLabel}
          </option>
        ))}
      </select>
    </label>
  );
}
