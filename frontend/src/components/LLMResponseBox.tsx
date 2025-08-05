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
      }, 20);

      return () => clearInterval(interval);
    }
  }, [llmResponse]);

  if (!llmResponse) return null;

  return (
    <div className="mb-6 animate-in fade-in duration-500">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          AI Assistant
        </h3>
        <div className="text-gray-700 leading-relaxed whitespace-pre-wrap text-justify font-inter">
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
  );
} 