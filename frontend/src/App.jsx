import { useState, useEffect } from 'react';
import { UploadCloud, Key, Download, Loader2, AlertCircle } from 'lucide-react';

function App() {
  const [apiKey, setApiKey] = useState('');
  const [file, setFile] = useState(null);
  const [mode, setMode] = useState('compounds');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!apiKey) {
      setError("Please provide your Google Gemini API Key.");
      return;
    }
    if (!file) {
      setError("Please upload a file (PDF or TXT).");
      return;
    }

    setLoading(true);

    const formData = new FormData();
    formData.append('api_key', apiKey);
    formData.append('mode', mode);
    formData.append('file', file);

    try {
      // In production, you would point this to your Cloud Run URL
      // For local testing, it assumes the backend runs on localhost:8000
      const apiUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000/generate';

      const response = await fetch(apiUrl, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Server error: ${response.status}`);
      }

      // Handle file download
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `biochemistry_${mode}.apkg`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl w-full space-y-8 bg-white p-10 rounded-xl shadow-lg border border-gray-100">

        <div>
          <h2 className="text-center text-3xl font-extrabold text-gray-900">
            Anki Biochemistry Deck Generator
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Upload your text or PDF notes to automatically generate Anki flashcards.
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>

          {/* API Key Input */}
          <div>
            <label htmlFor="api-key" className="block text-sm font-medium text-gray-700">
              Google Gemini API Key
            </label>
            <div className="mt-1 relative rounded-md shadow-sm">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Key className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="password"
                id="api-key"
                className="focus:ring-blue-500 focus:border-blue-500 block w-full pl-10 sm:text-sm border-gray-300 rounded-md p-2 border"
                placeholder="AIzaSy..."
                value={apiKey}
                onChange={handleKeyChange}
              />
            </div>
            <p className="mt-1 text-xs text-gray-500">Stored locally in your browser.</p>
          </div>

          {/* Mode Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Generation Mode</label>
            <div className="grid grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => setMode('compounds')}
                className={`p-4 border rounded-lg text-left focus:outline-none ${
                  mode === 'compounds' ? 'border-blue-500 ring-2 ring-blue-200 bg-blue-50' : 'border-gray-200 hover:border-blue-300'
                }`}
              >
                <div className="font-semibold text-gray-900">Standard Compounds</div>
                <div className="text-xs text-gray-500 mt-1">Extracts names & structures (RDKit)</div>
              </button>

              <button
                type="button"
                onClick={() => setMode('pathway')}
                className={`p-4 border rounded-lg text-left focus:outline-none ${
                  mode === 'pathway' ? 'border-blue-500 ring-2 ring-blue-200 bg-blue-50' : 'border-gray-200 hover:border-blue-300'
                }`}
              >
                <div className="font-semibold text-gray-900">Pathway Occlusion</div>
                <div className="text-xs text-gray-500 mt-1">Extracts pathways and creates image occlusions</div>
              </button>
            </div>
          </div>

          {/* File Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Upload Document (.pdf or .txt)</label>
            <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md hover:border-blue-400 transition-colors bg-gray-50">
              <div className="space-y-1 text-center">
                <UploadCloud className="mx-auto h-12 w-12 text-gray-400" />
                <div className="flex text-sm text-gray-600 justify-center">
                  <label
                    htmlFor="file-upload"
                    className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500 px-2 py-1"
                  >
                    <span>Choose a file</span>
                    <input id="file-upload" name="file-upload" type="file" className="sr-only" accept=".pdf,.txt" onChange={handleFileChange} />
                  </label>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  {file ? file.name : "No file selected"}
                </p>
              </div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <AlertCircle className="h-5 w-5 text-red-400" aria-hidden="true" />
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">Error</h3>
                  <div className="mt-2 text-sm text-red-700">
                    <p>{error}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Submit Button */}
          <div>
            <button
              type="submit"
              disabled={loading}
              className={`group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors ${
                loading ? 'opacity-70 cursor-not-allowed' : ''
              }`}
            >
              {loading ? (
                <>
                  <Loader2 className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" />
                  Generating Deck... (This may take a minute)
                </>
              ) : (
                <>
                  <Download className="-ml-1 mr-2 h-5 w-5 text-white" />
                  Generate & Download .apkg
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default App;
