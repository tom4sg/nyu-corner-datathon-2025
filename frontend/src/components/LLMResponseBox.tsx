'use client';

import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

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
    <div className="mb-8 animate-in fade-in duration-500">
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">
          AI Response
        </h3>
        <div className="text-gray-700 leading-relaxed text-justify font-inter [&_p]:mb-4 [&_p:last-child]:mb-0">
          <ReactMarkdown>
            {displayedText}
          </ReactMarkdown>
          {isTyping && (
            <span className="inline-block w-2 h-4 bg-indigo-500 ml-1 animate-pulse" />
          )}
        </div>
        <div className="text-sm text-gray-500">
          Based on your search for &quot;{query}&quot;
        </div>
      </div>
    </div>
  );
} 