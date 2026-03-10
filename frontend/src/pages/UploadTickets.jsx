import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { uploadTicket } from '../services/api';
import { ArrowLeft, Upload, FileText, CheckCircle, AlertCircle, Camera, FolderOpen, X } from 'lucide-react';
import imageCompression from 'browser-image-compression';

const UploadTickets = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [compressing, setCompressing] = useState(false);
  const [results, setResults] = useState([]);
  const [uploadProgress, setUploadProgress] = useState({ current: 0, total: 0 });

  const compressImageIfNeeded = async (file) => {
    if (!file.type.startsWith('image/')) return file;

    const triggerSize = 3 * 1024 * 1024;
    if (file.size < triggerSize) return file;

    console.log(`🔄 Comprimiendo ${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB)...`);

    try {
      const options = {
        maxSizeMB: 3,
        maxWidthOrHeight: 1920,
        useWebWorker: true,
        fileType: file.type
      };

      const compressedFile = await imageCompression(file, options);
      console.log(`✅ ${file.name}: ${(file.size/1024/1024).toFixed(2)}MB → ${(compressedFile.size/1024/1024).toFixed(2)}MB`);
      return compressedFile;
    } catch (error) {
      console.error('Error al comprimir:', error);
      return file;
    }
  };

  // append=true → acumula sobre los existentes (no reemplaza)
  const processFiles = async (selectedFiles, append = false) => {
    const hasLargeImages = selectedFiles.some(f =>
      f.type.startsWith('image/') && f.size > 3 * 1024 * 1024
    );

    let processedFiles;
    if (hasLargeImages) {
      setCompressing(true);
      processedFiles = await Promise.all(
        selectedFiles.map(file => compressImageIfNeeded(file))
      );
      setCompressing(false);
    } else {
      processedFiles = selectedFiles;
    }

    if (append) {
      // Evitar duplicados por nombre
      setFiles(prev => {
        const existingNames = new Set(prev.map(f => f.name));
        const newOnes = processedFiles.filter(f => !existingNames.has(f.name));
        return [...prev, ...newOnes];
      });
    } else {
      setFiles(processedFiles);
    }
  };

  const handleFileChange = async (e) => {
    await processFiles(Array.from(e.target.files), true); // append: conserva los anteriores
    e.target.value = ''; // reset para que onChange se dispare aunque elijas el mismo archivo
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    await processFiles(Array.from(e.dataTransfer.files), true); // append
  };

  // Quitar un archivo individual de la lista
  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      alert('Selecciona al menos un archivo');
      return;
    }

    setUploading(true);
    setUploadProgress({ current: 0, total: files.length });
    const newResults = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      setUploadProgress({ current: i + 1, total: files.length });

      try {
        const response = await uploadTicket(id, file);
        newResults.push({ file: file.name, success: true, data: response.data });
      } catch (error) {
        newResults.push({
          file: file.name,
          success: false,
          error: error.response?.data?.detail || 'Error al procesar'
        });
      }

      setResults([...newResults]);
    }

    setUploading(false);
    setUploadProgress({ current: 0, total: 0 });
  };

  const successCount = results.filter(r => r.success).length;

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

          {compressing && (
            <div className="mb-4 p-4 bg-blue-500/10 border border-blue-500/30 rounded-sm">
              <div className="flex items-center gap-3">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-400"></div>
                <p className="text-sm text-blue-400">
                  🔄 Comprimiendo imágenes... Esto puede tardar unos segundos
                </p>
              </div>
            </div>
          )}

          {/* Zona de drop */}
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            className="border-2 border-dashed border-zinc-700 hover:border-amber-500 rounded-sm p-12 text-center transition-colors"
          >
            <Upload size={48} className="mx-auto text-zinc-600 mb-4" />
            <p className="text-lg font-medium text-zinc-300 mb-2">
              Arrastra archivos aquí o elige una opción
            </p>
            <p className="text-sm text-zinc-500 mb-6 font-mono">
              Acepta: JPG, PNG, PDF • Imágenes grandes se comprimen automáticamente
            </p>

            <div className="flex flex-col sm:flex-row gap-3 justify-center max-w-md mx-auto">
              <input
                type="file"
                accept="image/*"
                capture="environment"
                multiple
                onChange={handleFileChange}
                className="hidden"
                id="camera-input"
              />
              <label
                htmlFor="camera-input"
                className="flex-1 flex items-center justify-center gap-2 bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-sm font-bold cursor-pointer transition-all shadow-lg shadow-blue-500/30"
              >
                <Camera size={20} />
                TOMAR FOTO
              </label>

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
                className="flex-1 flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-600 text-zinc-950 px-6 py-3 rounded-sm font-bold cursor-pointer transition-all shadow-lg shadow-amber-500/30"
              >
                <FolderOpen size={20} />
                ELEGIR ARCHIVOS
              </label>
            </div>
            <p className="text-xs text-zinc-600 mt-4">💡 "Tomar Foto" abre la cámara en móvil</p>
          </div>

          {/* Lista archivos seleccionados */}
          {files.length > 0 && (
            <div className="mt-6">
              <h3 className="font-semibold font-mono mb-3 tracking-wider">
                ARCHIVOS SELECCIONADOS ({files.length})
              </h3>
              <div className="space-y-2">
                {files.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-3 p-3 bg-zinc-950 border border-zinc-700 rounded-sm"
                  >
                    <FileText size={20} className="text-amber-500 flex-shrink-0" />
                    <span className="flex-1 text-sm truncate">{file.name}</span>
                    <span className="text-xs text-zinc-500 font-mono whitespace-nowrap">
                      {(file.size / 1024).toFixed(1)} KB
                    </span>
                    {/* Botón quitar archivo */}
                    <button
                      onClick={() => removeFile(index)}
                      disabled={uploading}
                      className="p-1 rounded-sm text-zinc-600 hover:text-red-400 hover:bg-zinc-800 transition-colors disabled:opacity-40"
                      title="Quitar archivo"
                    >
                      <X size={16} />
                    </button>
                  </div>
                ))}
              </div>

              <button
                onClick={handleUpload}
                disabled={uploading || compressing}
                className="w-full mt-4 bg-amber-500 hover:bg-amber-600 text-zinc-950 py-3 rounded-sm font-bold transition-all shadow-lg shadow-amber-500/30 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <Upload size={18} />
                {uploading
                  ? `PROCESANDO... (${uploadProgress.current}/${uploadProgress.total})`
                  : 'PROCESAR CON IA'
                }
              </button>

              {/* Barra de progreso animada */}
              {uploading && (
                <div className="mt-4 p-4 bg-zinc-950 border border-amber-500/30 rounded-sm space-y-3">
                  {/* Header con contador */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="relative">
                        <div className="animate-spin rounded-full h-5 w-5 border-2 border-amber-500 border-t-transparent"></div>
                      </div>
                      <span className="text-sm font-semibold text-zinc-100">
                        Procesando con IA...
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-lg font-bold text-amber-500">
                        {uploadProgress.current}/{uploadProgress.total}
                      </span>
                      <span className="text-xs text-zinc-500 ml-2">
                        {Math.round((uploadProgress.current / uploadProgress.total) * 100)}%
                      </span>
                    </div>
                  </div>

                  {/* Barra de progreso con gradiente */}
                  <div className="relative h-3 bg-zinc-800 rounded-full overflow-hidden">
                    <div
                      className="absolute inset-y-0 left-0 bg-gradient-to-r from-amber-600 via-amber-500 to-amber-400 transition-all duration-500 ease-out rounded-full"
                      style={{ width: `${(uploadProgress.current / uploadProgress.total) * 100}%` }}
                    >
                      {/* Efecto de brillo animado */}
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer"></div>
                    </div>

                    {/* Puntos de checkpoint cada 25% */}
                    <div className="absolute inset-0 flex items-center justify-between px-1">
                      {[25, 50, 75].map(percent => (
                        <div
                          key={percent}
                          className={`w-1 h-1 rounded-full ${
                            (uploadProgress.current / uploadProgress.total) * 100 >= percent
                              ? 'bg-white'
                              : 'bg-zinc-700'
                          }`}
                        />
                      ))}
                    </div>
                  </div>

                  {/* Mensaje descriptivo */}
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-amber-500">🤖</span>
                    <span className="text-zinc-400">
                      Analizando facturas y extrayendo datos automáticamente
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Resultados */}
          {results.length > 0 && (
            <div className="mt-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold font-mono tracking-wider">RESULTADOS</h3>
                <span className="text-sm text-zinc-400 font-mono">
                  {successCount} de {results.length} exitosos
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
                      {result.success
                        ? <CheckCircle size={20} className="text-green-400 flex-shrink-0 mt-0.5" />
                        : <AlertCircle size={20} className="text-red-400 flex-shrink-0 mt-0.5" />
                      }
                      <div className="flex-1">
                        <p className="font-medium text-sm mb-1">{result.file}</p>
                        {result.success ? (
                          <div className="text-xs space-y-1 font-mono text-zinc-400">
                            <p>
                              <span className="font-medium">Proveedor:</span>{' '}
                              {result.data?.provider || 'N/A'}
                            </p>
                            <p>
                              <span className="font-medium">Total:</span>{' '}
                              {result.data?.final_total ? `${result.data.final_total}€` : 'N/A'}
                            </p>
                            <p>
                              <span className="font-medium">Tipo:</span>{' '}
                              {result.data?.type === 'factura' ? 'Factura' : 'Ticket'}
                            </p>
                            {result.data?.is_foreign && (
                              <div className="mt-2 pt-2 border-t border-blue-500/30">
                                <p className="text-blue-400 font-bold mb-1">
                                  🌍 Factura internacional detectada
                                </p>
                                <p>
                                  <span className="font-medium">Divisa:</span>{' '}
                                  <span className="bg-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded text-xs">
                                    {result.data.currency || 'N/A'}
                                  </span>
                                </p>
                                {result.data.country_code && (
                                  <p>
                                    <span className="font-medium">País:</span>{' '}
                                    {result.data.country_code}
                                  </p>
                                )}
                              </div>
                            )}
                          </div>
                        ) : (
                          <p className="text-xs text-red-400">
                            {typeof result.error === 'string'
                              ? result.error
                              : JSON.stringify(result.error)
                            }
                          </p>
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

      {/* CSS para animación shimmer */}
      <style>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        .animate-shimmer {
          animation: shimmer 2s infinite;
        }
      `}</style>
    </div>
  );
};

export default UploadTickets;
