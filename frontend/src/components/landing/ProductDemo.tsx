"use client";

import React, { useState, useEffect, useRef } from "react";
import { 
  Play, 
  Pause, 
  AlertTriangle, 
  CheckCircle2, 
  Sparkles, 
  FileText, 
  ExternalLink,
  ChevronRight,
  Info,
  Clock,
  Video,
  Volume2,
  VolumeX,
  Maximize2,
  RotateCcw,
  FileEdit
} from "lucide-react";

export default function ProductDemo() {
  const [activeChapter, setActiveChapter] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [progress, setProgress] = useState<number>(15);
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [currentTime, setCurrentTime] = useState<number>(15);
  const totalDuration = 90; // 1 min 30 seconds

  const chapters = [
    {
      id: 0,
      title: "1. Inconsistency Detection",
      icon: <AlertTriangle className="w-4 h-4 text-amber-600" />,
      timeRange: [0, 25],
      caption: "CONVELINA cross-compares extracted details across documents and highlights clerical variations in name formatting or date of birth.",
    },
    {
      id: 1,
      title: "2. AI Procedure Guidance",
      icon: <Sparkles className="w-4 h-4 text-blue-600" />,
      timeRange: [25, 55],
      caption: "The AI assistant provides step-by-step guidance on official correction procedures grounded in verified government circulars.",
    },
    {
      id: 2,
      title: "3. Official Forms Repository",
      icon: <FileText className="w-4 h-4 text-emerald-600" />,
      timeRange: [55, 75],
      caption: "Direct access to authentic government forms (such as Form 49A and Joint Declarations) with clear prerequisites.",
    },
    {
      id: 3,
      title: "4. Correction Drafts",
      icon: <FileEdit className="w-4 h-4 text-purple-600" />,
      timeRange: [75, 90],
      caption: "Generate pre-filled correction letter and affidavit drafts ready to download in PDF or DOCX format for your submission.",
    },
  ];

  // Video progress timer
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isPlaying) {
      interval = setInterval(() => {
        setCurrentTime((prev) => {
          if (prev >= totalDuration) {
            setIsPlaying(false);
            return totalDuration;
          }
          const nextTime = prev + 1;
          setProgress((nextTime / totalDuration) * 100);

          // Update active chapter based on time
          const currentChapter = chapters.find(
            (c) => nextTime >= c.timeRange[0] && nextTime < c.timeRange[1]
          );
          if (currentChapter && currentChapter.id !== activeChapter) {
            setActiveChapter(currentChapter.id);
          }
          return nextTime;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isPlaying, activeChapter, totalDuration]);

  const selectChapter = (chapterId: number) => {
    setActiveChapter(chapterId);
    const startSec = chapters[chapterId].timeRange[0];
    setCurrentTime(startSec);
    setProgress((startSec / totalDuration) * 100);
  };

  const handlePlayToggle = () => {
    if (currentTime >= totalDuration) {
      setCurrentTime(0);
      setProgress(0);
      setActiveChapter(0);
    }
    setIsPlaying(!isPlaying);
  };

  const formatTime = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const remainingSecs = Math.floor(secs % 60);
    return `${mins}:${remainingSecs < 10 ? "0" : ""}${remainingSecs}`;
  };

  return (
    <section id="preview" className="py-20 md:py-28 bg-[#f5f3ef]/50 border-b border-[#e5e2dc]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
        {/* Section Header */}
        <div className="text-center space-y-3 max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white border border-[#e5e2dc] text-xs font-semibold uppercase tracking-wider text-zinc-700 shadow-xs">
            <Video className="w-3.5 h-3.5 text-zinc-900" />
            <span>Product Demonstration</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-serif text-[#18181b]">
            See CONVELINA in action.
          </h2>
          <p className="text-sm sm:text-base text-zinc-600 leading-relaxed">
            Watch how the platform compares documents, identifies discrepancies, and guides you step-by-step through official correction channels.
          </p>
        </div>

        {/* Video Player Frame */}
        <div className="bg-white border border-[#e5e2dc] rounded-2xl shadow-elevated overflow-hidden">
          {/* Top Browser Bar */}
          <div className="px-5 py-3.5 bg-[#faf9f6] border-b border-[#e5e2dc] flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <span className="w-3 h-3 rounded-full bg-zinc-300 border border-zinc-400/40" />
              <span className="w-3 h-3 rounded-full bg-zinc-300 border border-zinc-400/40" />
              <span className="w-3 h-3 rounded-full bg-zinc-300 border border-zinc-400/40" />
              <span className="ml-3 px-3 py-1 rounded-md bg-white border border-[#e5e2dc] text-xs font-mono text-zinc-600">
                https://convelina.app/app
              </span>
            </div>

            <div className="flex items-center gap-2 text-xs text-zinc-500 font-medium">
              <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>Live Application Preview</span>
            </div>
          </div>

          {/* Chapter Navigation Tabs */}
          <div className="flex border-b border-[#e5e2dc] bg-zinc-50/70 overflow-x-auto">
            {chapters.map((ch) => (
              <button
                key={ch.id}
                onClick={() => selectChapter(ch.id)}
                className={`flex-1 min-w-[170px] py-3.5 px-4 text-xs sm:text-sm font-medium text-center border-b-2 transition flex items-center justify-center gap-2 ${
                  activeChapter === ch.id
                    ? "border-[#18181b] text-[#18181b] bg-white font-semibold shadow-xs"
                    : "border-transparent text-zinc-500 hover:text-zinc-900 hover:bg-zinc-100/50"
                }`}
              >
                {ch.icon}
                <span>{ch.title}</span>
              </button>
            ))}
          </div>

          {/* Video Demonstration Stage */}
          <div className="relative p-6 sm:p-8 md:p-10 min-h-[460px] bg-white flex flex-col justify-between">
            {/* VIEW 1: INCONSISTENCY DETECTION */}
            {activeChapter === 0 && (
              <div className="space-y-6 animate-in fade-in duration-300">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-zinc-100 gap-2">
                  <div>
                    <h3 className="text-base sm:text-lg font-semibold text-zinc-900">Document Comparison Analysis</h3>
                    <p className="text-xs sm:text-sm text-zinc-500">Cross-comparing extracted details between Aadhaar and PAN Card</p>
                  </div>
                  <span className="self-start sm:self-auto px-3 py-1 rounded-full text-xs font-medium bg-amber-50 text-amber-800 border border-amber-200">
                    1 Discrepancy Found
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  {/* Document Card A */}
                  <div className="p-5 rounded-xl border border-[#e5e2dc] bg-[#faf9f6]/70 space-y-3.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider text-zinc-800">Aadhaar Card</span>
                      <span className="text-xs font-mono text-zinc-500">Masked: XXXX-XXXX-4819</span>
                    </div>
                    <div className="space-y-2 text-xs sm:text-sm">
                      <div className="flex justify-between py-1 border-b border-zinc-200/60">
                        <span className="text-zinc-500">Name:</span>
                        <span className="font-medium text-zinc-900">Ramanathan Kumar</span>
                      </div>
                      <div className="flex justify-between py-1 border-b border-zinc-200/60">
                        <span className="text-zinc-500">Date of Birth:</span>
                        <span className="font-medium text-zinc-900">14/08/1988</span>
                      </div>
                      <div className="flex justify-between py-1">
                        <span className="text-zinc-500">Gender:</span>
                        <span className="font-medium text-zinc-900">Male</span>
                      </div>
                    </div>
                  </div>

                  {/* Document Card B */}
                  <div className="p-5 rounded-xl border border-amber-300 bg-amber-50/40 space-y-3.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider text-amber-900">PAN Card</span>
                      <span className="text-xs font-mono text-amber-800">ABCDE1234F</span>
                    </div>
                    <div className="space-y-2 text-xs sm:text-sm">
                      <div className="flex justify-between py-1 border-b border-amber-200/60">
                        <span className="text-amber-800/80">Name:</span>
                        <span className="font-bold text-amber-950 bg-amber-200/60 px-1.5 py-0.5 rounded">
                          K. Ramanathan
                        </span>
                      </div>
                      <div className="flex justify-between py-1 border-b border-amber-200/60">
                        <span className="text-amber-800/80">Date of Birth:</span>
                        <span className="font-medium text-zinc-900">14/08/1988</span>
                      </div>
                      <div className="flex justify-between py-1">
                        <span className="text-amber-800/80">Gender:</span>
                        <span className="font-medium text-zinc-900">Male</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Explanation Card */}
                <div className="p-4 rounded-xl bg-amber-50/60 border border-amber-200/80 flex items-start gap-3 text-xs sm:text-sm text-amber-900">
                  <Info className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold">Analysis: </span>
                    Initial expansion detected. The name on your PAN card uses an initial (<span className="font-semibold">K. Ramanathan</span>) while Aadhaar records the full name (<span className="font-semibold">Ramanathan Kumar</span>). Both records share the exact same Date of Birth.
                  </div>
                </div>
              </div>
            )}

            {/* VIEW 2: AI PROCEDURE GUIDANCE */}
            {activeChapter === 1 && (
              <div className="space-y-6 animate-in fade-in duration-300">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-zinc-100 gap-2">
                  <div>
                    <h3 className="text-base sm:text-lg font-semibold text-zinc-900">Official Procedure Assistant</h3>
                    <p className="text-xs sm:text-sm text-zinc-500">Step-by-step guidance grounded strictly in verified government regulations</p>
                  </div>
                  <span className="self-start sm:self-auto px-3 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-800 border border-blue-200">
                    Official Guidance
                  </span>
                </div>

                <div className="space-y-4">
                  {/* User Question */}
                  <div className="flex items-start gap-3 justify-end">
                    <div className="p-4 rounded-2xl rounded-tr-none bg-[#18181b] text-white text-xs sm:text-sm max-w-xl shadow-xs">
                      How do I resolve the name mismatch between my Aadhaar (full name) and PAN card (initial)? Which document should I update?
                    </div>
                  </div>

                  {/* AI Response */}
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shrink-0 shadow-xs">
                      <Sparkles className="w-4 h-4" />
                    </div>
                    <div className="p-5 rounded-2xl rounded-tl-none bg-[#faf9f6] border border-[#e5e2dc] text-xs sm:text-sm text-zinc-800 max-w-2xl space-y-3 shadow-xs">
                      <p className="leading-relaxed">
                        Under Income Tax Department guidelines, your PAN record should match your Aadhaar proof of identity. Since your Aadhaar contains your full expanded name, submitting a <strong>PAN Correction Request (Form 49A)</strong> is the standard procedure.
                      </p>
                      <div className="p-3 bg-white rounded-xl border border-[#e5e2dc] space-y-1.5 text-xs">
                        <div className="font-semibold text-zinc-900">Recommended Next Steps:</div>
                        <ul className="list-disc list-inside text-zinc-600 space-y-1">
                          <li>Submit an online PAN correction via Protean (NSDL) or UTIITSL portal.</li>
                          <li>Select your Aadhaar as Proof of Identity (POI) and Proof of Date of Birth (DOB).</li>
                          <li>No newspaper publication is required when expanding a recognized initial.</li>
                        </ul>
                      </div>
                      <div className="text-[11px] text-zinc-500 pt-1 border-t border-zinc-200/50">
                        Source Reference: Income Tax PAN Allotment & Rectification Guidelines (Rule 114)
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* VIEW 3: OFFICIAL FORMS */}
            {activeChapter === 2 && (
              <div className="space-y-6 animate-in fade-in duration-300">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-zinc-100 gap-2">
                  <div>
                    <h3 className="text-base sm:text-lg font-semibold text-zinc-900">Verified Official Forms & Portals</h3>
                    <p className="text-xs sm:text-sm text-zinc-500">Direct access to official government forms cross-referenced with your situation</p>
                  </div>
                  <span className="self-start sm:self-auto text-xs text-zinc-500">
                    Direct Download & Official Links
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div className="p-5 rounded-xl border border-[#e5e2dc] bg-[#faf9f6]/70 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold text-zinc-900">FORM-49A</span>
                      <span className="text-xs px-2 py-0.5 bg-zinc-200/80 rounded text-zinc-700">Income Tax / NSDL</span>
                    </div>
                    <h4 className="text-xs sm:text-sm font-medium text-zinc-800">PAN Correction / Change Request Application</h4>
                    <p className="text-xs text-zinc-500 leading-relaxed">
                      Used to rectify misspelled names, expand initials, or update birth dates in existing PAN records.
                    </p>
                    <div className="pt-2 flex items-center justify-between text-xs font-semibold text-zinc-800 border-t border-zinc-200/60">
                      <span>Requires: Aadhaar POI + Class 10 Certificate</span>
                      <span className="inline-flex items-center gap-1 text-blue-600 hover:underline">
                        Open Portal <ExternalLink className="w-3 h-3" />
                      </span>
                    </div>
                  </div>

                  <div className="p-5 rounded-xl border border-[#e5e2dc] bg-[#faf9f6]/70 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold text-zinc-900">EPFO-JD-2024</span>
                      <span className="text-xs px-2 py-0.5 bg-zinc-200/80 rounded text-zinc-700">EPFO India</span>
                    </div>
                    <h4 className="text-xs sm:text-sm font-medium text-zinc-800">EPFO Joint Declaration Form</h4>
                    <p className="text-xs text-zinc-500 leading-relaxed">
                      Mandatory joint submission between employee and employer to rectify UAN and PF profile parameters.
                    </p>
                    <div className="pt-2 flex items-center justify-between text-xs font-semibold text-zinc-800 border-t border-zinc-200/60">
                      <span>Requires: Employer Signature & Aadhaar</span>
                      <span className="inline-flex items-center gap-1 text-blue-600 hover:underline">
                        Open Portal <ExternalLink className="w-3 h-3" />
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* VIEW 4: CORRECTION DRAFTS */}
            {activeChapter === 3 && (
              <div className="space-y-6 animate-in fade-in duration-300">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-zinc-100 gap-2">
                  <div>
                    <h3 className="text-base sm:text-lg font-semibold text-zinc-900">Pre-filled Correction Drafts</h3>
                    <p className="text-xs sm:text-sm text-zinc-500">Standardized affidavit and request drafts generated with required legal justifications</p>
                  </div>
                  <span className="self-start sm:self-auto px-3 py-1 rounded-full text-xs font-medium bg-purple-50 text-purple-800 border border-purple-200">
                    Ready to Download
                  </span>
                </div>

                <div className="p-5 rounded-xl border border-[#e5e2dc] bg-[#faf9f6]/70 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <FileEdit className="w-5 h-5 text-purple-600" />
                      <span className="text-sm font-bold text-zinc-900">Name Correction Sworn Affidavit Draft</span>
                    </div>
                    <span className="text-xs font-mono text-zinc-500">Format: PDF / DOCX</span>
                  </div>

                  <div className="p-4 bg-white rounded-lg border border-[#e5e2dc] text-xs font-mono text-zinc-700 space-y-2 leading-relaxed">
                    <p>BEFORE THE EXECUTIVE MAGISTRATE / NOTARY PUBLIC</p>
                    <p>I, Ramanathan Kumar (also recorded as K. Ramanathan in PAN ABCDE1234F), S/o [Father Name], residing at [Address], do hereby solemnly affirm and state as follows:</p>
                    <p>1. That my name is Ramanathan Kumar as correctly evidenced by Aadhaar XXXX-XXXX-4819.</p>
                    <p>2. That the initial &apos;K.&apos; on my PAN card stands for my surname and both identities represent the same person...</p>
                  </div>

                  <div className="pt-1 flex items-center justify-between text-xs text-zinc-600">
                    <span>Includes official statutory disclaimer and placeholder highlights.</span>
                    <span className="font-semibold text-purple-700">Exportable as PDF & DOCX</span>
                  </div>
                </div>
              </div>
            )}

            {/* Captions Subtitle Bar */}
            <div className="mt-8 p-3.5 rounded-xl bg-zinc-900 text-white text-xs sm:text-sm flex items-center gap-3">
              <span className="w-2 h-2 rounded-full bg-emerald-400 shrink-0" />
              <p className="flex-1 font-normal text-zinc-200">
                {chapters[activeChapter].caption}
              </p>
            </div>
          </div>

          {/* Video Control Bar */}
          <div className="px-5 py-4 bg-[#faf9f6] border-t border-[#e5e2dc] flex flex-col gap-3">
            {/* Scrub / Progress Bar */}
            <div 
              className="w-full h-2 bg-zinc-200 rounded-full overflow-hidden cursor-pointer relative"
              onClick={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                const pos = (e.clientX - rect.left) / rect.width;
                const newTime = Math.floor(pos * totalDuration);
                setCurrentTime(newTime);
                setProgress(pos * 100);
              }}
            >
              <div 
                className="h-full bg-[#18181b] rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>

            {/* Control Buttons & Timers */}
            <div className="flex items-center justify-between text-xs text-zinc-700">
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={handlePlayToggle}
                  className="w-8 h-8 rounded-lg bg-[#18181b] text-white flex items-center justify-center hover:bg-zinc-800 transition shadow-xs"
                  aria-label={isPlaying ? "Pause demonstration" : "Play demonstration"}
                >
                  {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 ml-0.5" />}
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setCurrentTime(0);
                    setProgress(0);
                    setActiveChapter(0);
                    setIsPlaying(true);
                  }}
                  className="p-1.5 rounded-md text-zinc-600 hover:text-black hover:bg-zinc-200/50 transition"
                  title="Replay from start"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>

                <div className="font-mono text-xs text-zinc-600 font-medium">
                  {formatTime(currentTime)} / {formatTime(totalDuration)}
                </div>
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setIsMuted(!isMuted)}
                  className="p-1.5 rounded-md text-zinc-600 hover:text-black hover:bg-zinc-200/50 transition"
                  aria-label={isMuted ? "Unmute" : "Mute"}
                >
                  {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                </button>

                <button
                  type="button"
                  onClick={() => {
                    const elem = document.getElementById("preview");
                    if (elem) {
                      if (!document.fullscreenElement) {
                        elem.requestFullscreen?.().catch(() => {});
                      } else {
                        document.exitFullscreen?.().catch(() => {});
                      }
                    }
                  }}
                  className="p-1.5 rounded-md text-zinc-600 hover:text-black hover:bg-zinc-200/50 transition"
                  title="Fullscreen preview"
                >
                  <Maximize2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
