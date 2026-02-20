import { useState, useCallback, useRef, useEffect } from "react";
import { Copy, Trash2, Sparkles, Loader2, BookOpen } from "lucide-react";

const QUICK_LENGTHS = [
  { label: "مختصر", value: 150 },
  { label: "درمیانی", value: 300 },
  { label: "طویل", value: 450 }
];

// Use environment variable only, no hardcoded fallback for production
const API_URL = import.meta.env.VITE_API_URL;
if (!API_URL) console.warn("VITE_API_URL is not set! Make sure to define it in Vercel environment variables.");

const Index = () => {
  const [inputText, setInputText] = useState("");
  const [outputWords, setOutputWords] = useState<string[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [maxLength, setMaxLength] = useState(300);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const outputRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef(false);

  const streamWords = useCallback((text: string) => {
    const words = text.split(/\s+/).filter(Boolean);
    setOutputWords([]);
    setIsStreaming(true);
    abortRef.current = false;
    let i = 0;

    const interval = setInterval(() => {
      if (abortRef.current) {
        clearInterval(interval);
        setIsStreaming(false);
        return;
      }
      if (i < words.length) {
        setOutputWords((prev) => [...prev, words[i]]);
        i++;
      } else {
        clearInterval(interval);
        setIsStreaming(false);
      }
    }, 50);
  }, []);

  const handleGenerate = useCallback(async () => {
    if (!inputText.trim()) {
      setError("براہ کرم پہلے کہانی شروع کرنے کے لیے ایک جملہ لکھیں۔");
      return;
    }
    setError("");
    setIsGenerating(true);
    setOutputWords([]);

    try {
      const response = await fetch(`${API_URL}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prefix: inputText,
          max_length: maxLength
        })
      });

      if (!response.ok) throw new Error("API error");

      const data = await response.json();
      const storyText = data.generated_text || data.text;
      if (!storyText) throw new Error("No story returned from API");

      streamWords(storyText);

    } catch (err) {
      console.error("Story generation failed:", err);
      setError("کہانی بنانا ممکن نہیں تھا، دوبارہ کوشش کریں۔");
    } finally {
      setIsGenerating(false);
    }
  }, [inputText, maxLength, streamWords]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.ctrlKey && e.key === "Enter") {
      handleGenerate();
    }
  };

  const handleCopy = () => {
    const text = outputWords.join(" ");
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleClear = () => {
    abortRef.current = true;
    setInputText("");
    setOutputWords([]);
    setError("");
    setIsStreaming(false);
    setIsGenerating(false);
  };

  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [outputWords]);

  return (
    <div className="min-h-screen bg-gradient-main relative overflow-hidden">
      <div className="absolute top-[-20%] right-[-10%] w-[500px] h-[500px] rounded-full bg-primary/10 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-20%] left-[-10%] w-[400px] h-[400px] rounded-full bg-secondary/10 blur-[100px] pointer-events-none" />
      <div className="absolute top-[40%] left-[50%] w-[300px] h-[300px] rounded-full bg-accent/5 blur-[80px] pointer-events-none" />

      <div className="relative z-10 container max-w-3xl mx-auto px-4 py-8 md:py-12 my-[5px]">
        <header className="text-center mb-10">
          <div className="inline-flex items-start gap-3 mb-4 overflow-visible min-h-[120px] sm:min-h-[140px] md:min-h-[160px]">
            <BookOpen className="w-8 h-8 text-accent animate-float mt-4" />
            <h1 className="font-urdu text-3xl sm:text-4xl md:text-5xl font-bold text-gradient leading-[4] py-6 overflow-visible">
              ​اردو کہانی جنریٹر
            </h1>
            <Sparkles className="w-8 h-8 text-accent animate-float mt-4" style={{ animationDelay: "1s" }} />
          </div>
          <p className="font-urdu text-lg text-muted-foreground leading-[2.2]">
            AI سے بچوں کے لیے اردو کہانیاں بنائیں
          </p>
        </header>

        <div className="glass rounded-2xl p-6 md:p-8 glow-primary space-y-6">
          <div>
            <textarea
              dir="rtl"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="کہانی شروع کرنے کے لیے ایک جملہ لکھیں..."
              className="font-urdu w-full min-h-[120px] bg-input/50 border border-border rounded-xl p-4 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all duration-300 resize-none text-lg leading-[2.2]" />
            <p className="text-xs text-muted-foreground mt-1 text-left" dir="ltr">
              Ctrl + Enter to generate
            </p>
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="font-urdu text-sm text-muted-foreground leading-[2]">
                  زیادہ سے زیادہ لمبائی
                </label>
                <span className="text-sm font-medium text-accent">{maxLength}</span>
              </div>
              <input
                type="range"
                min={50}
                max={500}
                value={maxLength}
                onChange={(e) => setMaxLength(Number(e.target.value))}
                className="w-full h-2 rounded-full appearance-none cursor-pointer bg-muted accent-primary [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary [&::-webkit-slider-thumb]:shadow-lg" />
            </div>

            <div className="flex gap-2 justify-end" dir="rtl">
              {QUICK_LENGTHS.map((ql) =>
                <button
                  key={ql.value}
                  onClick={() => setMaxLength(ql.value)}
                  className={`font-urdu text-sm py-1.5 px-4 rounded-lg border transition-all duration-200 leading-[2] ${
                    maxLength === ql.value ?
                      "bg-primary/20 border-primary text-primary-foreground" :
                      "border-border text-muted-foreground hover:border-primary/50 hover:text-foreground"}`
                  }>
                  {ql.label} ({ql.value})
                </button>
              )}
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className={`font-urdu flex-1 py-3 px-6 rounded-xl text-lg font-bold bg-gradient-primary text-primary-foreground transition-all duration-300 hover:opacity-90 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed leading-[2.2] ${
                !isGenerating ? "animate-pulse-glow" : ""}`}
            >
              {isGenerating ?
                <span className="flex items-center justify-center gap-2">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>کہانی بنائی جا رہی ہے...</span>
                </span> :
                "📖 کہانی بنائیں"
              }
            </button>

            <button
              onClick={handleClear}
              className="py-3 px-4 rounded-xl border border-border text-muted-foreground hover:text-foreground hover:border-primary/50 transition-all duration-300"
              title="صاف کریں">
              <Trash2 className="w-5 h-5" />
            </button>
          </div>

          {error &&
            <div className="font-urdu text-destructive bg-destructive/10 border border-destructive/20 rounded-xl p-3 text-center leading-[2.2]">
              {error}
            </div>
          }

          {(outputWords.length > 0 || isStreaming) &&
            <div className="relative">
              <div className="flex items-center justify-between mb-2">
                <span className="font-urdu text-sm text-muted-foreground leading-[2]">کہانی</span>
                {outputWords.length > 0 &&
                  <button
                    onClick={handleCopy}
                    className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-accent transition-colors duration-200">
                    <Copy className="w-3.5 h-3.5" />
                    {copied ? "کاپی ہو گیا!" : "کاپی کریں"}
                  </button>
                }
              </div>
              <div
                ref={outputRef}
                dir="rtl"
                className="font-urdu bg-input/30 border border-border rounded-xl p-5 min-h-[150px] max-h-[400px] overflow-y-auto text-lg leading-[2.4] text-foreground">
                {outputWords.map((word, i) =>
                  <span
                    key={i}
                    className="animate-word-in inline"
                    style={{ animationDelay: `${i * 20}ms` }}>
                    {word}{" "}
                  </span>
                )}
                {isStreaming &&
                  <span className="inline-block w-0.5 h-5 bg-accent animate-cursor-blink align-middle mr-1" />
                }
              </div>
            </div>
          }

          {outputWords.length === 0 && !isStreaming && !error &&
            <div className="font-urdu text-center text-muted-foreground py-8 leading-[2.2]">
              یہاں آپ کی کہانی ظاہر ہوگی...
            </div>
          }
        </div>

        <footer className="text-center mt-8 text-xs text-muted-foreground">
          Powered by AI • اردو بچوں کی کہانی جنریٹر
        </footer>
      </div>
    </div>
  );
};

export default Index;