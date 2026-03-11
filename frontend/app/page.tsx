
'use client';

import { useState, useCallback, ChangeEvent } from 'react';
import { useDropzone } from 'react-dropzone';

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [email, setEmail] = useState<string>('');
  const [message, setMessage] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      setMessage('');
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    },
    maxFiles: 1,
  });

  const handleEmailChange = (e: ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value);
  };

  const handleSubmit = async () => {
    if (!file) {
      setMessage('Please upload a file.');
      return;
    }
    if (!email) {
      setMessage('Please enter a recipient email.');
      return;
    }

    setIsLoading(true);
    setMessage('Uploading and processing file...');

    const formData = new FormData();
    formData.append('file', file);

    try {
      // 1. Upload file
      const uploadResponse = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/upload`, {
        method: 'POST',
        headers: {
          'X-API-KEY': process.env.NEXT_PUBLIC_API_KEY || '',
        },
        body: formData,
      });

      if (!uploadResponse.ok) {
        const errorData = await uploadResponse.json();
        throw new Error(errorData.detail || 'File upload failed');
      }

      const uploadResult = await uploadResponse.json();
      setMessage(`File uploaded: ${uploadResult.filename}. Generating summary...`);

      // 2. Generate summary
      const summaryResponse = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/generate-summary`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-KEY': process.env.NEXT_PUBLIC_API_KEY || '',
        },
        body: JSON.stringify({ file_path: uploadResult.filename, client_email: email }), // Assuming backend can re-read or use a reference
      });

      if (!summaryResponse.ok) {
        const errorData = await summaryResponse.json();
        throw new Error(errorData.detail || 'Summary generation failed');
      }

      const summaryResult = await summaryResponse.json();
      const summaryContent = `
        Executive Summary: ${summaryResult.ai_summary.executive_summary}

        Key Insights:
        ${summaryResult.ai_summary.key_insights.map((insight: string) => `- ${insight}`).join('\n')}

        Warnings/Anomalies:
        ${summaryResult.ai_summary.warnings_anomalies.map((warning: string) => `- ${warning}`).join('\n')}

        Analytics:
        ${Object.entries(summaryResult.analytics).map(([key, value]: [string, any]) => `- ${key}: ${value}`).join('\n')}
      `;

      setMessage('Summary generated. Sending email...');

      // 3. Send email
      const emailResponse = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/send-email`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-KEY': process.env.NEXT_PUBLIC_API_KEY || '',
        },
        body: JSON.stringify({ recipient_email: email, summary_content: summaryContent }),
      });

      if (!emailResponse.ok) {
        const errorData = await emailResponse.json();
        throw new Error(errorData.detail || 'Email sending failed');
      }

      setMessage('Sales summary successfully sent via email!');
      setFile(null);
      setEmail('');
    } catch (error: any) {
      setMessage(`Error: ${error.message}`);
      console.error('Full error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
        <h1 className="text-2xl font-bold text-center mb-6">Sales Insight Automator</h1>

        <div
          {...getRootProps()}
          className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-gray-400 transition duration-300 ease-in-out mb-4"
        >
          <input {...getInputProps()} />
          {isDragActive ? (
            <p className="text-gray-600">Drop the files here ...</p>
          ) : (
            <p className="text-gray-600">Drag 'n' drop a sales file here, or click to select one (.csv, .xls, .xlsx)</p>
          )}
          {file && <p className="mt-2 text-sm text-gray-800">Selected file: {file.name}</p>}
        </div>

        <div className="mb-4">
          <label htmlFor="email" className="block text-gray-700 text-sm font-bold mb-2">
            Recipient Email:
          </label>
          <input
            type="email"
            id="email"
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            placeholder="Enter recipient email"
            value={email}
            onChange={handleEmailChange}
            required
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={isLoading || !file || !email}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline w-full disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Processing...' : 'Generate Summary & Send Email'}
        </button>

        {message && (
          <p className={`mt-4 text-center ${message.startsWith('Error') ? 'text-red-500' : 'text-green-500'}`}>
            {message}
          </p>
        )}
      </div>
    </div>
  );
}
