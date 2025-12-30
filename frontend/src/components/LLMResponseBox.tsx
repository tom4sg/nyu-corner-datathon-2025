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
          <ReactMarkdown
            components={{
              strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
              em: ({ children }) => <em className="italic">{children}</em>,
              code: ({ children }) => <code className="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">{children}</code>,
              h1: ({ children }) => <h1 className="text-2xl font-bold mt-4 mb-2">{children}</h1>,
              h2: ({ children }) => <h2 className="text-xl font-bold mt-3 mb-2">{children}</h2>,
              h3: ({ children }) => <h3 className="text-lg font-semibold mt-2 mb-1">{children}</h3>,
              ul: ({ children }) => <ul className="list-disc list-inside mb-4 space-y-1">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal list-inside mb-4 space-y-1">{children}</ol>,
              li: ({ children }) => <li className="ml-4">{children}</li>,
              p: ({ children, ...props }) => (
                <p {...props}>
                  {children}
                </p>
              ),
            }}
          >
            {displayedText}
          </ReactMarkdown>
          {isTyping && (
            <span className="inline-block w-0.5 h-4 bg-indigo-500 ml-0.5 animate-pulse" />
          )}
        </div>
        <div className="text-sm text-gray-500">
          Based on your search for &quot;{query}&quot;
        </div>
      </div>
    </div>
  );
}