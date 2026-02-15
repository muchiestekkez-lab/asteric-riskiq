/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Only proxy API calls in local development
  ...(process.env.NODE_ENV === 'development' && !process.env.NEXT_PUBLIC_API_URL
    ? {
        async rewrites() {
          return [
            {
              source: '/api/:path*',
              destination: 'http://localhost:8000/api/:path*',
            },
            {
              source: '/ws/:path*',
              destination: 'http://localhost:8000/ws/:path*',
            },
          ];
        },
      }
    : {}),
};

export default nextConfig;
