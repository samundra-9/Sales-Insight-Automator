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
      // Upload file
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

      // Generate summary
      const summaryForm = new FormData();
      summaryForm.append('file_path', uploadResult.filename);
      summaryForm.append('client_email', email);

      const summaryResponse = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/generate-summary`, {
        method: 'POST',
        headers: {
          'X-API-KEY': process.env.NEXT_PUBLIC_API_KEY || '',
        },
        body: summaryForm,
      });

      if (!summaryResponse.ok) {
        const errorData = await summaryResponse.json();
        throw new Error(errorData.detail || 'Summary generation failed');
      }

      const summaryResult = await summaryResponse.json();

      const summaryContent = `
Executive Summary:
${summaryResult.ai_summary.executive_summary}

Key Insights:
${summaryResult.ai_summary.key_insights
        .map((i: string) => `- ${i}`)
        .join('\n')}

Warnings / Anomalies:
${summaryResult.ai_summary.warnings_anomalies
        .map((w: string) => `- ${w}`)
        .join('\n')}

Analytics:
${Object.entries(summaryResult.analytics)
        .map(([k, v]) => `- ${k}: ${v}`)
        .join('\n')}
`;

      setMessage('Summary generated. Sending email...');

      // Send email
      const emailForm = new FormData();
      emailForm.append('recipient_email', email);
      emailForm.append('summary_content', summaryContent);

      const emailResponse = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/send-email`, {
        method: 'POST',
        headers: {
          'X-API-KEY': process.env.NEXT_PUBLIC_API_KEY || '',
        },
        body: emailForm,
      });

      if (!emailResponse.ok) {
        const errorData = await emailResponse.json();
        throw new Error(errorData.detail || 'Email sending failed');
      }

      setMessage('Sales summary successfully sent via email!');
      setFile(null);
      setEmail('');
    } catch (error: any) {
      console.error('Full error:', error);
      setMessage(`Error: ${error.message}`);
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
          className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-gray-400 transition mb-4"
        >
          <input {...getInputProps()} />

          {isDragActive ? (
            <p>Drop the file here...</p>
          ) : (
            <p>Drag & drop a sales file or click to select (.csv, .xls, .xlsx)</p>
          )}

          {file && (
            <p className="mt-2 text-sm">Selected: {file.name}</p>
          )}
        </div>

        <input
          type="email"
          placeholder="Recipient Email"
          value={email}
          onChange={handleEmailChange}
          className="border p-2 w-full mb-4"
        />

        <button
          onClick={handleSubmit}
          disabled={isLoading || !file || !email}
          className="bg-blue-500 text-white w-full py-2 rounded disabled:opacity-50"
        >
          {isLoading ? 'Processing...' : 'Generate Summary & Send Email'}
        </button>

        {message && (
          <p className="mt-4 text-center">{message}</p>
        )}
      </div>
    </div>
  );
}
