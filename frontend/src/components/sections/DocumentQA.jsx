import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Bot, Send, User, Sparkles } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { cn } from '@/lib/utils';

const DocumentQA = () => {
  const [messages, setMessages] = useState([
    { role: 'bot', content: "Once you've translated a document, you can ask me anything about it!" }
  ]);
  const [input, setInput] = useState('');
  const { toast } = useToast();
  const scrollAreaRef = useRef(null);

  useEffect(() => {
    if (scrollAreaRef.current) {
      // @ts-ignore
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');

    try {
      const selectedLangCode =
        (typeof window !== 'undefined' && window.localStorage.getItem('alibi_target_lang')) || 'auto';

      const payload: any = {
        message: userMessage.content,
        target_lang: selectedLangCode
      };

      const fileName =
        typeof window !== 'undefined' && window.localStorage.getItem('alibi_output_filename');
      if (fileName) {
        payload.image_filename = fileName; // 'translated.png'
      }

      const res = await fetch('http://localhost:8001/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();

      if (data?.target_lang && typeof window !== 'undefined') {
        window.localStorage.setItem('alibi_target_lang', data.target_lang);
      }

      const botMessage = { role: 'bot', content: data?.reply ?? 'No response' };
      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      console.error(err);
      toast({
        title: "Chatbot error",
        description: "Couldn't reach the QA service. Check the backend and try again.",
        variant: "destructive"
      });
      setMessages(prev => [...prev, { role: 'bot', content: "Sorry—I'm having trouble reaching the QA service." }]);
    }
  };

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
      className="my-16"
    >
      <Card className="glass-card w-full max-w-4xl mx-auto">
        <CardHeader className="text-center">
          <CardTitle className="flex items-center justify-center space-x-2 text-3xl font-bold">
            <Sparkles className="w-8 h-8 text-purple-400" />
            <span>Ask Your Document Anything</span>
          </CardTitle>
          <CardDescription>Get simple answers about your legal, financial, or medical documents.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="bg-black/20 border border-white/10 rounded-lg p-4 h-96 flex flex-col space-y-4">
            <div ref={scrollAreaRef} className="flex-grow overflow-y-auto pr-2 space-y-4">
              {messages.map((msg, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  className={cn("flex items-start gap-3", msg.role === 'user' ? 'justify-end' : 'justify-start')}
                >
                  {msg.role === 'bot' && (
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-600 to-indigo-600 flex items-center justify-center flex-shrink-0">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                  )}
                  <div className={cn("chat-bubble", msg.role === 'user' ? 'user' : 'bot')}>
                    {msg.content}
                  </div>
                  {msg.role === 'user' && (
                    <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center flex-shrink-0">
                      <User className="w-5 h-5 text-white" />
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
            <div className="flex items-center gap-2 border-t border-white/10 pt-4">
              <Input
                type="text"
                placeholder="e.g., 'What is the deadline mentioned on page 2?'"
                className="flex-grow bg-secondary border-white/20 focus:ring-purple-500"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              />
              <Button
                size="icon"
                onClick={handleSend}
                className="bg-purple-600 hover:bg-purple-700 text-white flex-shrink-0"
              >
                <Send className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.section>
  );
};

export default DocumentQA;