import { useState, useRef, useEffect, useCallback } from 'react';
import { showWarning } from '../utils/toast';

const useVoiceSearch = ({ lang = 'es-ES', onResult }) => {
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);
  const onResultRef = useRef(onResult);

  useEffect(() => {
    onResultRef.current = onResult;
  }, [onResult]);

  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SR();
      recognitionRef.current.lang = lang;
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        onResultRef.current(transcript);
        setIsListening(false);
      };
      recognitionRef.current.onerror = () => setIsListening(false);
      recognitionRef.current.onend = () => setIsListening(false);
    }
  }, [lang]);

  const startVoiceSearch = useCallback(() => {
    if (recognitionRef.current) {
      setIsListening(true);
      recognitionRef.current.start();
    } else {
      showWarning('Tu navegador no soporta búsqueda por voz');
    }
  }, []);

  return { isListening, startVoiceSearch };
};

export default useVoiceSearch;
