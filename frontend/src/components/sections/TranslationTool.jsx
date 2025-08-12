import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileImage, Languages, Loader2, CheckCircle, X, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Select } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/components/ui/use-toast';
import { SUPPORTED_LANGUAGES } from '@/lib/languages';

const TranslationTool = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [isLoading, setIsLoading] = useState(false);
  const [translatedImage, setTranslatedImage] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);
  const { toast } = useToast();

  const handleFileSelect = (file) => {
    if (!file) return;
    const validTypes = ['image/jpeg', 'image/png', 'image/jpg'];
    if (!validTypes.includes(file.type)) {
      toast({
        title: "Invalid file type",
        description: "Please upload a JPEG or PNG image.",
        variant: "destructive"
      });
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      toast({
        title: "File too large",
        description: "Please upload an image smaller than 10MB.",
        variant: "destructive"
      });
      return;
    }
    setSelectedFile(file);
    setTranslatedImage(null);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    handleFileSelect(e.dataTransfer.files[0]);
  };

  const handleDragOver = (e) => { e.preventDefault(); setDragOver(true); };
  const handleDragLeave = (e) => { e.preventDefault(); setDragOver(false); };
  const handleFileInputChange = (e) => handleFileSelect(e.target.files[0]);

  const handleTranslate = async () => {
    if (!selectedFile) {
      toast({
        title: "No file selected",
        description: "Please upload an image first.",
        variant: "destructive"
      });
      return;
    }

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('image', selectedFile);
      formData.append('targetLanguage', selectedLanguage);

      const response = await fetch('http://localhost:8000/upload-image', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const result = await response.blob();
      const imageUrl = URL.createObjectURL(result);
      setTranslatedImage(imageUrl);

      // 🔗 Share with chatbot (language + known output filename)
      if (typeof window !== 'undefined') {
        window.localStorage.setItem('alibi_target_lang', selectedLanguage);
        window.localStorage.setItem('alibi_output_filename', 'translated.png'); // Flask writes this fixed name
      }

      toast({
        title: "Translation completed!",
        description: "Your document has been successfully translated."
      });
    } catch (error) {
      console.error('Translation error:', error);
      toast({
        title: "Translation failed",
        description: "There was a problem translating your document.",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const clearFile = () => {
    setSelectedFile(null);
    setTranslatedImage(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}>
        <Card className="h-full glass-card">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Upload className="w-5 h-5 text-purple-400" />
              <span>1. Upload Document</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className={`upload-area rounded-lg p-8 text-center cursor-pointer ${dragOver ? 'dragover' : ''}`}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onClick={() => fileInputRef.current?.click()}>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/jpg"
                onChange={handleFileInputChange}
                className="hidden"
              />
              {selectedFile ? (
                <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="space-y-4">
                  <CheckCircle className="w-12 h-12 text-green-400 mx-auto" />
                  <div className="bg-background/50 rounded-lg p-3 border border-white/10">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3 overflow-hidden">
                        <FileImage className="w-6 h-6 text-purple-400 flex-shrink-0" />
                        <p className="font-medium text-gray-200 truncate">{selectedFile.name}</p>
                      </div>
                      <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); clearFile(); }}>
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </motion.div>
              ) : (
                <div className="space-y-4 text-gray-400">
                  <Upload className="w-12 h-12 mx-auto text-gray-500" />
                  <p className="font-medium text-gray-300">Drop image here or <span className="text-purple-400">browse</span></p>
                  <p className="text-sm">Supports JPEG, PNG up to 10MB</p>
                </div>
              )}
            </div>
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-300">Target Language</label>
              <Select value={selectedLanguage} onChange={(e) => setSelectedLanguage(e.target.value)} className="bg-secondary border-white/20">
                {SUPPORTED_LANGUAGES.map((lang) => (
                  <option key={lang.code} value={lang.code}>{lang.name}</option>
                ))}
              </Select>
            </div>
            <Button onClick={handleTranslate} disabled={!selectedFile || isLoading}
              className="w-full h-12 text-lg font-semibold bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white shine-effect">
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Translating...
                </>
              ) : (
                <>
                  <Languages className="w-5 h-5 mr-2" />
                  Translate Document
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }}>
        <Card className="h-full glass-card">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <FileImage className="w-5 h-5 text-purple-400" />
              <span>2. Review Translation</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-black/20 rounded-lg p-4 min-h-[32rem] flex items-center justify-center border border-white/10">
              <AnimatePresence mode="wait">
                {isLoading ? (
                  <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="text-center space-y-4 text-gray-400">
                    <div className="loading-spinner mx-auto"></div>
                    <p className="text-lg font-medium text-gray-300">AI is translating...</p>
                  </motion.div>
                ) : translatedImage ? (
                  <motion.div key="translated" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="w-full space-y-4">
                    <img src={translatedImage} alt="Translated document" className="w-full h-auto rounded-lg shadow-lg" />
                    <Button onClick={() => {
                      const link = document.createElement('a');
                      link.href = translatedImage;
                      link.download = `translated-${selectedFile?.name || 'document'}`;
                      link.click();
                    }} className="w-full bg-green-600 hover:bg-green-700 text-white">
                      <Download className="w-4 h-4 mr-2" />
                      Download
                    </Button>
                  </motion.div>
                ) : selectedFile ? (
                  <motion.div key="preview" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="w-full">
                    <img src={URL.createObjectURL(selectedFile)} alt="Document preview" className="w-full h-auto rounded-lg shadow-lg" />
                  </motion.div>
                ) : (
                  <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center space-y-4 text-gray-500">
                    <FileImage className="w-16 h-16 mx-auto" />
                    <p className="font-medium text-gray-400">Preview will appear here</p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default TranslationTool;