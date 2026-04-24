import { useStore } from '../store';
import { cn, formatElapsed } from '../lib/cn';
import { Circle, Clock, Settings, History, MessageSquare, FileText, Radio } from 'lucide-react';
import { UserButton } from '@clerk/chrome-extension';

export function TopBar() {
  const { view, isCapturing, isPaused, elapsedSec, setView } = useStore();

  return (
    <header className="border-b border-surface-border bg-surface-muted px-4 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="grid h-8 w-8 place-items-center rounded-lg bg-brand-600 text-white">
            <Radio className="h-4 w-4" />
          </div>
          <div>
            <div className="text-sm font-semibold">MeetingMate</div>
            <div className="flex items-center gap-2 text-xs text-zinc-400">
              {isCapturing ? (
                <>
                  <span className="flex items-center gap-1 text-red-400">
                    <Circle className="h-2 w-2 animate-pulse fill-red-400" />
                    AI Assistant Active
                  </span>
                  <span className="text-zinc-500">·</span>
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatElapsed(elapsedSec)}
                    {isPaused && <span className="ml-1 text-amber-400">(paused)</span>}
                  </span>
                </>
              ) : (
                <span>Ready</span>
              )}
            </div>
          </div>
        </div>
        <UserButton afterSignOutUrl="/" />
      </div>

      <nav className="mt-3 flex items-center gap-1 text-xs">
        <TabBtn active={view === 'live'} onClick={() => setView('live')} icon={<Radio className="h-3.5 w-3.5" />}>
          Live
        </TabBtn>
        <TabBtn active={view === 'notes'} onClick={() => setView('notes')} icon={<FileText className="h-3.5 w-3.5" />}>
          Notes
        </TabBtn>
        <TabBtn
          active={view === 'chat'}
          onClick={() => setView('chat')}
          icon={<MessageSquare className="h-3.5 w-3.5" />}
        >
          Chat
        </TabBtn>
        <TabBtn
          active={view === 'history'}
          onClick={() => setView('history')}
          icon={<History className="h-3.5 w-3.5" />}
        >
          History
        </TabBtn>
        <TabBtn
          active={view === 'settings'}
          onClick={() => setView('settings')}
          icon={<Settings className="h-3.5 w-3.5" />}
        >
          Settings
        </TabBtn>
      </nav>
    </header>
  );
}

function TabBtn({
  active,
  icon,
  children,
  onClick,
}: {
  active: boolean;
  icon: React.ReactNode;
  children: React.ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'flex items-center gap-1.5 rounded-md px-2.5 py-1.5 transition-colors',
        active ? 'bg-brand-600 text-white' : 'text-zinc-300 hover:bg-surface-soft',
      )}
    >
      {icon}
      <span>{children}</span>
    </button>
  );
}
