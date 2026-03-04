import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { uploadTicket } from '../services/api';
import { ArrowLeft, Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react';

const UploadTickets = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState([]);

  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files));
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setFiles(Array.from(e.dataTransfer.files));
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      alert('Selecciona al menos un archivo');
      return;
    }

    setUploading(true);
    const newResults = [];

    for (const file of files) {
      try {
        const response = await uploadTicket(id, file);
        newResults.push({
          file: file.name,
          success: true,
          data: response.data
        });
      } catch (error) {
        newResults.push({
          file: file.name,
          success: false,
          error: error.response?.data?.detail || 'Error al procesar'
        });
      }
    }

    setResults(newResults);
    setUploading(false);
  };

  const successCount = results.filter(r => r.success).length;
  const totalCount = results.length;

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4">
          <button
            onClick={() => navigate(`/projects/${id}`)}
            className="flex items-center gap-2 text-zinc-400 hover:text-zinc-100 transition-colors mb-3"
          >
            <ArrowLeft size={18} />
            <span className="text-sm">Volver</span>
          </button>
          <h1 className="text-3xl font-bebas tracking-wider">SUBIR TICKETS</h1>
        </div>
      </div>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-8">
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            className="border-2 border-dashed border-zinc-700 hover:border-amber-500 rounded-sm p-12 text-center transition-colors"
          >
            <Upload size={48} className="mx-auto text-zinc-600 mb-4" />
            <p className="text-lg font-medium text-zinc-300 mb-2">
              Arrastra archivos aquí o haz click para seleccionar
            </p>
            <p className="text-sm text-zinc-500 mb-4 font-mono">
              Acepta: JPG, PNG, PDF
            </p>
            <input
              type="file"
              accept="image/*,.pdf"
              multiple
              onChange={handleFileChange}
              className="hidden"
              id="file-upload"
            />
            <label
              htmlFor="file-upload"
              className="inline-block bg-amber-500 hover:bg-amber-600 text-zinc-950 px-6 py-3 rounded-sm font-bold cursor-pointer transition-all shadow-lg shadow-amber-500/30"
            >
              SELECCIONAR ARCHIVOS
            </label>
          </div>

          {files.length > 0 && (
            <div className="mt-6">
              <h3 className="font-semibold font-mono mb-3 tracking-wider">ARCHIVOS SELECCIONADOS ({files.length})</h3>
              <div className="space-y-2">
                {files.map((file, index) => (
                  <div key={index} className="flex items-center gap-3 p-3 bg-zinc-950 border border-zinc-700 rounded-sm">
                    <FileText size={20} className="text-amber-500" />
                    <span className="flex-1 text-sm">{file.name}</span>
                    <span className="text-xs text-zinc-500 font-mono">
                      {(file.size / 1024).toFixed(1)} KB
                    </span>
                  </div>
                ))}
              </div>

              <button
                onClick={handleUpload}
                disabled={uploading}
                className="w-full mt-4 bg-amber-500 hover:bg-amber-600 text-zinc-950 py-3 rounded-sm font-bold transition-all shadow-lg shadow-amber-500/30 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <Upload size={18} />
                {uploading ? `PROCESANDO... (${results.length}/${files.length})` : 'PROCESAR CON IA'}
              </button>
            </div>
          )}

          {results.length > 0 && (
            <div className="mt-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold font-mono tracking-wider">RESULTADOS</h3>
                <span className="text-sm text-zinc-400 font-mono">
                  {successCount} de {totalCount} exitosos
                </span>
              </div>
              
              <div className="space-y-3">
                {results.map((result, index) => (
                  <div
                    key={index}
                    className={`p-4 rounded-sm border-2 ${
                      result.success
                        ? 'border-green-500/30 bg-green-500/10'
                        : 'border-red-500/30 bg-red-500/10'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      {result.success ? (
                        <CheckCircle size={20} className="text-green-400 flex-shrink-0 mt-0.5" />
                      ) : (
                        <AlertCircle size={20} className="text-red-400 flex-shrink-0 mt-0.5" />
                      )}
                      <div className="flex-1">
                        <p className="font-medium text-sm mb-1">{result.file}</p>
                        {result.success ? (
                          <div className="text-xs space-y-1 font-mono text-zinc-400">
                            <p><span className="font-medium">Proveedor:</span> {result.data.provider}</p>
                            <p><span className="font-medium">Total:</span> {result.data.final_total}€</p>
                            <p><span className="font-medium">Tipo:</span> {result.data.type === 'factura' ? 'Factura' : 'Ticket'}</p>
                          </div>
                        ) : (
                          <p className="text-xs text-red-400">{result.error}</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {successCount > 0 && (
                <button
                  onClick={() => navigate(`/projects/${id}`)}
                  className="w-full mt-4 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 py-3 rounded-sm font-semibold transition-colors"
                >
                  VER PROYECTO
                </button>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default UploadTickets;
