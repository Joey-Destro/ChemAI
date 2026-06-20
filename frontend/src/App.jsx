import { useState, useEffect } from 'react';
import { UploadCloud, Key, Download, Loader2, AlertCircle, FileText, CheckCircle2, FlaskConical, Network, Type } from 'lucide-react';

function App() {
  const [apiKey, setApiKey] = useState('');
  const [file, setFile] = useState(null);
  const [textContent, setTextContent] = useState('');
  const [inputType, setInputType] = useState('file'); // 'file' or 'text'
  const [mode, setMode] = useState('compounds');
  const [subject, setSubject] = useState('Lékařská biochemie');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    const savedKey = localStorage.getItem('geminiApiKey');
    if (savedKey) {
      setApiKey(savedKey);
    }
  }, []);

  const handleKeyChange = (e) => {
    const newKey = e.target.value;
    setApiKey(newKey);
    localStorage.setItem('geminiApiKey', newKey);
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setSuccess(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    if (!apiKey) {
      setError("Please provide your Google Gemini API Key.");
      return;
    }
    if (inputType === 'file' && !file) {
      setError("Please upload a file (PDF or TXT).");
      return;
    }
    if (inputType === 'text' && !textContent.trim()) {
      setError("Please enter some text.");
      return;
    }

    setLoading(true);

    const formData = new FormData();
    formData.append('api_key', apiKey);
    formData.append('mode', mode);
    formData.append('subject', subject);
    if (inputType === 'file') {
      formData.append('file', file);
    } else {
      formData.append('text_content', textContent);
    }

    try {
      const apiUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8080/generate';

      let response;
      try {
        response = await fetch(apiUrl, {
          method: 'POST',
          body: formData,
        });
      } catch (networkError) {
        throw new Error(
          `Failed to connect to the backend server at ${apiUrl}. ` +
          `If you are running this locally, ensure you have started the backend with 'uvicorn main:app --port 8080' or via docker. ` +
          `If this is deployed, ensure VITE_BACKEND_URL is set correctly.`
        );
      }

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Server error: ${response.status}`);
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `biochemistry_${mode}.apkg`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
      setSuccess(true);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-slate-900 flex flex-col items-center py-12 px-4 sm:px-6 lg:px-8 font-sans text-slate-100">

      {/* Decorative Background Elements */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-purple-600/20 blur-[120px]"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-blue-600/20 blur-[120px]"></div>
      </div>

      <div className="relative z-10 w-full max-w-3xl">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center p-3 bg-white/10 rounded-2xl backdrop-blur-md border border-white/10 shadow-xl mb-4">
            <FlaskConical className="w-8 h-8 text-purple-300 mr-2" />
            <Network className="w-8 h-8 text-blue-300" />
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-purple-300 to-blue-300">
            Synapse Deck
          </h1>
          <p className="mt-4 text-lg text-slate-300 max-w-xl mx-auto font-light">
            AI-powered Anki flashcard generation for any subject. Transform your PDFs into highly visual learning tools instantly.
          </p>
        </div>

        {/* Main Card */}
        <div className="bg-slate-800/50 backdrop-blur-xl rounded-3xl p-8 sm:p-10 shadow-2xl border border-slate-700/50">
          <form className="space-y-8" onSubmit={handleSubmit}>

            {/* API Key Section */}
            <div className="space-y-3">
              <label htmlFor="api-key" className="block text-sm font-medium text-slate-300">
                Gemini 1.5 Flash API Key
              </label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Key className="h-5 w-5 text-slate-500 group-focus-within:text-purple-400 transition-colors" />
                </div>
                <input
                  type="password"
                  id="api-key"
                  className="block w-full pl-11 pr-4 py-3 bg-slate-900/50 border border-slate-700 rounded-xl text-slate-200 placeholder-slate-500 focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 transition-all outline-none"
                  placeholder="AIzaSy..."
                  value={apiKey}
                  onChange={handleKeyChange}
                />
              </div>
            </div>

            {/* Subject Selection */}
            <div className="space-y-3">
              <label htmlFor="subject" className="block text-sm font-medium text-slate-300">
                Předmět / Obor
              </label>
              <div className="relative group">
                <input
                  type="text"
                  id="subject"
                  className="block w-full px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-xl text-slate-200 placeholder-slate-500 focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 transition-all outline-none"
                  placeholder="např. Lékařská biochemie, Anatomie..."
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                />
              </div>
            </div>

            {/* Mode Selection */}
            <div className="space-y-3">
              <label className="block text-sm font-medium text-slate-300">Generation Mode</label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <button
                  type="button"
                  onClick={() => setMode('compounds')}
                  className={`relative overflow-hidden p-5 rounded-2xl text-left transition-all duration-200 ${
                    mode === 'compounds'
                    ? 'bg-gradient-to-br from-purple-600/20 to-blue-600/20 border-2 border-purple-500/50 shadow-[0_0_15px_rgba(168,85,247,0.15)]'
                    : 'bg-slate-900/40 border-2 border-transparent hover:bg-slate-800/60 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center mb-2">
                    <FlaskConical className={`w-5 h-5 mr-2 ${mode === 'compounds' ? 'text-purple-400' : 'text-slate-400'}`} />
                    <span className={`font-semibold ${mode === 'compounds' ? 'text-purple-300' : 'text-slate-300'}`}>Compounds</span>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">Extracts chemical names and generates perfect 2D RDKit structures.</p>
                </button>

                <button
                  type="button"
                  onClick={() => setMode('pathway')}
                  className={`relative overflow-hidden p-5 rounded-2xl text-left transition-all duration-200 ${
                    mode === 'pathway'
                    ? 'bg-gradient-to-br from-blue-600/20 to-cyan-600/20 border-2 border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.15)]'
                    : 'bg-slate-900/40 border-2 border-transparent hover:bg-slate-800/60 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center mb-2">
                    <Network className={`w-5 h-5 mr-2 ${mode === 'pathway' ? 'text-blue-400' : 'text-slate-400'}`} />
                    <span className={`font-semibold ${mode === 'pathway' ? 'text-blue-300' : 'text-slate-300'}`}>Pathways</span>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">Maps full metabolic graphs and creates image-occlusion flashcards.</p>
                </button>
              </div>
            </div>

            {/* Input Selection */}
            <div className="space-y-3">
              <div className="flex justify-between items-end">
                <label className="block text-sm font-medium text-slate-300">Source Document</label>
                <div className="flex space-x-1 bg-slate-900/50 p-1 rounded-lg border border-slate-700/50">
                  <button
                    type="button"
                    onClick={() => setInputType('file')}
                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                      inputType === 'file' ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    File Upload
                  </button>
                  <button
                    type="button"
                    onClick={() => setInputType('text')}
                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                      inputType === 'text' ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Paste Text
                  </button>
                </div>
              </div>

              {inputType === 'file' ? (
                <div className="relative group">
                  <div className={`flex justify-center px-6 pt-8 pb-10 border-2 border-dashed rounded-2xl transition-all ${
                    file ? 'border-purple-500/50 bg-purple-900/10' : 'border-slate-700 hover:border-slate-500 hover:bg-slate-800/30 bg-slate-900/40'
                  }`}>
                    <div className="space-y-3 text-center">
                      {file ? (
                        <FileText className="mx-auto h-12 w-12 text-purple-400" />
                      ) : (
                        <UploadCloud className="mx-auto h-12 w-12 text-slate-500 group-hover:text-slate-400 transition-colors" />
                      )}
                      <div className="flex text-sm text-slate-400 justify-center">
                        <label
                          htmlFor="file-upload"
                          className="relative cursor-pointer rounded-md font-medium text-purple-400 hover:text-purple-300 focus-within:outline-none transition-colors"
                        >
                          <span>{file ? 'Change file' : 'Browse to upload'}</span>
                          <input id="file-upload" name="file-upload" type="file" className="sr-only" accept=".pdf,.txt" onChange={handleFileChange} />
                        </label>
                        {!file && <span className="pl-1">or drag and drop</span>}
                      </div>
                      <p className="text-xs text-slate-500">
                        {file ? <span className="text-slate-300 font-medium">{file.name}</span> : "PDF or TXT up to 10MB"}
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="relative">
                  <div className="absolute top-3 left-3 flex items-center pointer-events-none">
                    <Type className="h-5 w-5 text-slate-500" />
                  </div>
                  <textarea
                    rows={6}
                    className="block w-full pl-11 pr-4 py-3 bg-slate-900/50 border border-slate-700 rounded-xl text-slate-200 placeholder-slate-500 focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 transition-all outline-none resize-y"
                    placeholder="Paste your biochemistry text here..."
                    value={textContent}
                    onChange={(e) => {
                      setTextContent(e.target.value);
                      setError(null);
                      setSuccess(false);
                    }}
                  />
                </div>
              )}
            </div>

            {/* Feedback Messages */}
            {error && (
              <div className="rounded-xl bg-red-900/30 border border-red-500/30 p-4 flex items-start">
                <AlertCircle className="h-5 w-5 text-red-400 mt-0.5 flex-shrink-0" />
                <div className="ml-3 text-sm text-red-300 leading-relaxed">
                  {error}
                </div>
              </div>
            )}

            {success && !error && !loading && (
              <div className="rounded-xl bg-green-900/30 border border-green-500/30 p-4 flex items-start">
                <CheckCircle2 className="h-5 w-5 text-green-400 mt-0.5 flex-shrink-0" />
                <div className="ml-3 text-sm text-green-300 leading-relaxed">
                  Deck generated successfully! Your download should begin automatically.
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className={`w-full flex justify-center items-center py-4 px-4 border border-transparent text-base font-semibold rounded-xl text-white transition-all shadow-lg ${
                loading
                ? 'bg-slate-700 cursor-not-allowed opacity-80'
                : 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 hover:shadow-purple-500/25'
              }`}
            >
              {loading ? (
                <>
                  <Loader2 className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" />
                  Generating Synapses...
                </>
              ) : (
                <>
                  <Download className="-ml-1 mr-2 h-5 w-5 text-white" />
                  Synthesize Deck
                </>
              )}
            </button>

          </form>
        </div>

        {/* Footer */}
        <p className="mt-8 text-center text-xs text-slate-500">
          All processing is handled ephemerally. Files are deleted immediately after generation.
        </p>
      </div>
    </div>
  );
}

export default App;
