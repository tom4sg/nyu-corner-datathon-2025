'use client';

import { useState, useEffect } from 'react';

interface LLMResponseBoxProps {
  llmResponse: string;
  query: string;
}

export default function LLMResponseBox({ llmResponse, query }: LLMResponseBoxProps) {
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    if (llmResponse) {
      setIsTyping(true);
      setDisplayedText('');
      
      let index = 0;
      const interval = setInterval(() => {
        if (index < llmResponse.length) {
          setDisplayedText(llmResponse.slice(0, index + 1));
          index++;
        } else {
          setIsTyping(false);
          clearInterval(interval);
        }
      }, 20); // Adjust speed as needed

      return () => clearInterval(interval);
    }
  }, [llmResponse]);

  if (!llmResponse) return null;

  return (
    <div className="bg-indigo-50 border-l-4 border-indigo-400 rounded-xl p-6 mb-6 shadow-sm animate-in fade-in duration-500">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center">
            <span className="text-indigo-600 text-sm">💬</span>
          </div>
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            AI Assistant
          </h3>
          <div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
            {displayedText}
            {isTyping && (
              <span className="inline-block w-2 h-4 bg-indigo-500 ml-1 animate-pulse"></span>
            )}
          </div>
          <div className="mt-3 text-sm text-gray-500">
            Here&apos;s what matches your vibe for &quot;{query}&quot;
          </div>
        </div>
      </div>
    </div>
  );
} 