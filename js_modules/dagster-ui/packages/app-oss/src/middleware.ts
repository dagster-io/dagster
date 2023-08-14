import {NextResponse} from 'next/server';
import type {NextRequest} from 'next/server';

// This middleware only runs in dev mode.

export function middleware(request: NextRequest) {
  if (shouldProxy(request)) {
    console.log('proxying request', request.nextUrl.href);
    return NextResponse.rewrite(
      new URL(
        request.nextUrl.pathname,
        process.env.NEXT_PUBLIC_BACKEND_ORIGIN ?? 'http://localhost:3000',
      ),
    );
  } else {
    return NextResponse.next();
  }
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
};

// Behavior copied from CRA during CRA -> Next.js transition
// https://github.com/facebook/create-react-app/blob/0a827f69ab0d2ee3871ba9b71350031d8a81b7ae/packages/react-dev-utils/WebpackDevServerUtils.js#L368

function shouldProxy(request: NextRequest) {
  return request.method !== 'GET' || request.headers.get('Accept')?.indexOf('text/html') === -1;
}
