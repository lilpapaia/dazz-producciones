import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { uploadTicket } from '../services/api';
import { ArrowLeft, Upload, CheckCircle, AlertCircle } from 'lucide-react';
import imageCompression from 'browser-image-compression';

const UploadTickets = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0, status: '', percentage: 0 });
  const [results, setResults] = useState([]);

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    setSelectedFiles(files);
    setResults([]);
  };

  const compressImageIfNeeded = async (file) => {
    // Solo comprimir imágenes, no PDFs
    if (!file.type.startsWith('image/')) {
      return file;
    }

    const fileSizeMB = file.size / (1024 * 1024);
    
    // Si es menor de 3MB, no comprimir
    if (fileSizeMB < 3) {
      return file;
    }

    try {
      const options = {
        maxSizeMB: 3,
        maxWidthOrHeight: 1920,
        useWebWorker: true,
      };
      
      const compressedFile = await imageCompression(file, options);
      return compressedFile;
    } catch (error) {
      console.error('Error comprimiendo imagen:', error);
      return file; // Si falla, usar original
    }
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;

    setUploading(true);
    setResults([]);
    const uploadResults = [];
    
    for (let i = 0; i < selectedFiles.length; i++) {
      const file = selectedFiles[i];
      const fileNumber = i + 1;
      const totalFiles = selectedFiles.length;
      
      try {
        // Estado: Preparando
        setProgress({
          current: fileNumber,
          total: totalFiles,
          status: `Preparando ${file.name}...`,
          percentage: 10,
          phase: 'preparing'
        });

        // Comprimir si es necesario
        let processedFile = file;
        if (file.type.startsWith('image/')) {
          const fileSizeMB = file.size / (1024 * 1024);
          if (fileSizeMB > 3) {
            setProgress({
              current: fileNumber,
              total: totalFiles,
              status: `Comprimiendo ${file.name}...`,
              percentage: 20,
              phase: 'compressing'
            });
            processedFile = await compressImageIfNeeded(file);
          }
        }

        // Estado: Subiendo
        setProgress({
          current: fileNumber,
          total: totalFiles,
          status: `Subiendo ${file.name}...`,
          percentage: 40,
          phase: 'uploading'
        });

        // Estado: Procesando con IA
        setProgress({
          current: fileNumber,
          total: totalFiles,
          status: `Procesando con IA...`,
          percentage: 60,
          phase: 'processing'
        });

        // Subir archivo
        await uploadTicket(projectId, processedFile);

        // Estado: Completado
        setProgress({
          current: fileNumber,
          total: totalFiles,
          status: `✓ ${file.name} procesado`,
          percentage: 100,
          phase: 'completed'
        });

        uploadResults.push({
          name: file.name,
          success: true
        });

        // Pausa breve para que se vea el éxito
        await new Promise(resolve => setTimeout(resolve, 300));

      } catch (error) {
        console.error(`Error subiendo ${file.name}:`, error);
        uploadResults.push({
          name: file.name,
          success: false,
          error: error.response?.data?.detail || error.message
        });

        setProgress({
          current: fileNumber,
          total: totalFiles,
          status: `✗ Error: ${file.name}`,
          percentage: 100,
          phase: 'error'
        });

        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }

    setResults(uploadResults);
    setUploading(false);
    setProgress({ current: 0, total: 0, status: '', percentage: 0 });

    // Si todos exitosos, volver tras 1.5s
    if (uploadResults.every(r => r.success)) {
      setTimeout(() => {
        navigate(`/projects/${projectId}`);
      }, 1500);
    }
  };

  const getPhaseColor = (phase) => {
    switch (phase) {
      case 'preparing': return 'bg-blue-500';
      case 'compressing': return 'bg-purple-500';
      case 'uploading': return 'bg-yellow-500';
      case 'processing': return 'bg-amber-500';
      case 'completed': return 'bg-green-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-zinc-500';
    }
  };

  const getPhaseIcon = (phase) => {
    switch (phase) {
      case 'completed': return '✓';
      case 'error': return '✗';
      case 'processing': return '🤖';
      case 'uploading': return '📤';
      case 'compressing': return '🗜️';
      default: return '⏳';
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* Header */}
      <div className="border-b border-zinc-800 bg-zinc-900 sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4">
          <button
            onClick={() => navigate(`/projects/${projectId}`)}
            className="flex items-center gap-2 text-zinc-400 hover:text-zinc-100 transition-colors mb-3"
          >
            <ArrowLeft size={18} />
            <span className="text-sm">Volver al proyecto</span>
          </button>
          <h1 className="text-3xl font-bebas tracking-wider">SUBIR TICKETS</h1>
        </div>
      </div>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 pt-8 pb-12">
        <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-8">
          
          {/* Selector de archivos */}
          <div className="space-y-6">
            <div>
              <label className="block text-xs font-mono text-zinc-400 mb-3 tracking-wider">
                SELECCIONAR ARCHIVOS (JPG, PNG, PDF)
              </label>
              <input
                type="file"
                multiple
                accept="image/jpeg,image/jpg,image/png,application/pdf"
                onChange={handleFileSelect}
                disabled={uploading}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-3 text-zinc-100
                  file:mr-4 file:py-2 file:px-4 file:rounded-sm file:border-0
                  file:bg-amber-500 file:text-zinc-950 file:font-semibold
                  hover:file:bg-amber-600 file:cursor-pointer
                  disabled:opacity-50 disabled:cursor-not-allowed"
              />
            </div>

            {/* Lista de archivos seleccionados */}
            {selectedFiles.length > 0 && (
              <div className="bg-zinc-950 border border-zinc-700 rounded-sm p-4">
                <p className="text-xs font-mono text-zinc-400 mb-3">
                  {selectedFiles.length} ARCHIVO{selectedFiles.length > 1 ? 'S' : ''} SELECCIONADO{selectedFiles.length > 1 ? 'S' : ''}
                </p>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {selectedFiles.map((file, idx) => (
                    <div key={idx} className="flex items-center gap-3 text-sm">
                      <div className="text-amber-500">
                        {file.type === 'application/pdf' ? '📄' : '🖼️'}
                      </div>
                      <span className="flex-1 text-zinc-300 truncate">{file.name}</span>
                      <span className="text-xs text-zinc-500">
                        {(file.size / 1024 / 1024).toFixed(1)} MB
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Botón de subida */}
            <button
              onClick={handleUpload}
              disabled={selectedFiles.length === 0 || uploading}
              className="w-full px-6 py-4 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm
                transition-all shadow-lg shadow-amber-500/30 disabled:opacity-50 disabled:cursor-not-allowed
                flex items-center justify-center gap-3 text-lg"
            >
              <Upload size={24} />
              {uploading ? 'PROCESANDO...' : 'PROCESAR CON IA'}
            </button>

            {/* BARRA DE PROGRESO */}
            {uploading && progress.percentage > 0 && (
              <div className="space-y-3 animate-in fade-in duration-300">
                {/* Contador de archivos */}
                <div className="flex items-center justify-between text-sm">
                  <span className="text-zinc-400">
                    Archivo {progress.current} de {progress.total}
                  </span>
                  <span className="text-amber-400 font-mono">
                    {progress.percentage}%
                  </span>
                </div>

                {/* Barra de progreso */}
                <div className="relative h-3 bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className={`absolute inset-y-0 left-0 ${getPhaseColor(progress.phase)} 
                      transition-all duration-500 ease-out rounded-full`}
                    style={{ width: `${progress.percentage}%` }}
                  >
                    {/* Efecto de brillo animado */}
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent 
                      animate-shimmer" style={{
                        backgroundSize: '200% 100%',
                        animation: 'shimmer 2s infinite'
                      }}
                    />
                  </div>
                </div>

                {/* Estado actual */}
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-2xl">{getPhaseIcon(progress.phase)}</span>
                  <span className="text-zinc-300">{progress.status}</span>
                </div>
              </div>
            )}

            {/* Resultados */}
            {results.length > 0 && (
              <div className="bg-zinc-950 border border-zinc-700 rounded-sm p-4 space-y-2">
                <p className="text-xs font-mono text-zinc-400 mb-3">RESULTADOS</p>
                {results.map((result, idx) => (
                  <div
                    key={idx}
                    className={`flex items-start gap-3 p-3 rounded-sm ${
                      result.success
                        ? 'bg-green-500/10 border border-green-500/30'
                        : 'bg-red-500/10 border border-red-500/30'
                    }`}
                  >
                    {result.success ? (
                      <CheckCircle size={20} className="text-green-400 mt-0.5" />
                    ) : (
                      <AlertCircle size={20} className="text-red-400 mt-0.5" />
                    )}
                    <div className="flex-1">
                      <p className={`text-sm font-semibold ${
                        result.success ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {result.name}
                      </p>
                      {result.error && (
                        <p className="text-xs text-red-400 mt-1">{result.error}</p>
                      )}
                    </div>
                  </div>
                ))}

                {results.every(r => r.success) && (
                  <div className="text-center pt-2">
                    <p className="text-sm text-green-400">
                      ✓ Todos los archivos procesados correctamente
                    </p>
                    <p className="text-xs text-zinc-500 mt-1">
                      Redirigiendo al proyecto...
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>

      {/* CSS para animación shimmer */}
      <style>{`
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
        .animate-shimmer {
          animation: shimmer 2s infinite;
        }
      `}</style>
    </div>
  );
};

export default UploadTickets;
