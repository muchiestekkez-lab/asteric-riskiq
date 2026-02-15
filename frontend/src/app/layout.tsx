import type { Metadata } from 'next';
import './globals.css';
import { AuthProvider } from '@/lib/auth-context';
import AuthLayout from '@/components/layout/AuthLayout';

export const metadata: Metadata = {
  title: 'Asteric RiskIQ - Hospital Readmission Prediction AI',
  description: 'Advanced AI-powered hospital readmission risk prediction for partner hospitals',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <AuthLayout>{children}</AuthLayout>
        </AuthProvider>
      </body>
    </html>
  );
}
