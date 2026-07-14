/**
 * TopicTree — collapsible accordion tree for chapters and topics.
 * Shows chapter > topic > subtopic hierarchy with expand/collapse.
 */
import { useState } from 'react';
import { ChevronRight, ChevronDown, BookOpen, FileText, Layers } from 'lucide-react';

interface TreeNode {
  id: string;
  title: string;
  title_en?: string;
  unit_type: 'chapter' | 'topic' | 'subtopic';
  display_order: number;
  children?: TreeNode[];
}

interface TopicTreeProps {
  nodes: TreeNode[];
  onTopicClick?: (topicId: string, topicTitle: string) => void;
}

const TYPE_ICONS: Record<string, React.ReactNode> = {
  chapter: <BookOpen size={14} className="text-brand-400" />,
  topic: <Layers size={14} className="text-purple-400" />,
  subtopic: <FileText size={14} className="text-emerald-400" />,
};

const TYPE_STYLES: Record<string, string> = {
  chapter: 'hover:bg-brand-500/5 border-brand-500/10',
  topic: 'hover:bg-purple-500/5 border-purple-500/10 ml-4',
  subtopic: 'hover:bg-emerald-500/5 border-emerald-500/10 ml-8',
};

function TreeItem({ node, onTopicClick }: { node: TreeNode; onTopicClick?: (id: string, title: string) => void }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const hasChildren = node.children && node.children.length > 0;
  const style = TYPE_STYLES[node.unit_type] || '';

  const handleClick = () => {
    if (hasChildren) {
      setIsExpanded(!isExpanded);
    } else if (onTopicClick) {
      onTopicClick(node.id, node.title);
    }
  };

  return (
    <div>
      <button
        onClick={handleClick}
        className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg border border-transparent
                    text-left transition-all duration-200 group ${style}`}
      >
        {/* Expand/collapse or leaf indicator */}
        <div className="flex-shrink-0 w-4">
          {hasChildren ? (
            isExpanded ? (
              <ChevronDown size={14} className="text-white/40" />
            ) : (
              <ChevronRight size={14} className="text-white/40" />
            )
          ) : (
            <span className="w-1.5 h-1.5 rounded-full bg-white/10 block mx-auto" />
          )}
        </div>

        {/* Type icon */}
        {TYPE_ICONS[node.unit_type]}

        {/* Title */}
        <div className="flex-1 min-w-0">
          <span className="text-sm font-marathi text-white/80 group-hover:text-white transition-colors truncate block">
            {node.title}
          </span>
          {node.title_en && (
            <span className="text-[10px] text-white/25 block">{node.title_en}</span>
          )}
        </div>

        {/* Unit type badge */}
        <span className="text-[9px] px-2 py-0.5 rounded-full bg-white/5 text-white/30 flex-shrink-0">
          {node.unit_type === 'chapter' ? 'अध्याय' : 
           node.unit_type === 'topic' ? 'विषय' : 'उपविषय'}
        </span>
      </button>

      {/* Children */}
      {hasChildren && isExpanded && (
        <div className="animate-fade-in">
          {node.children!
            .sort((a, b) => a.display_order - b.display_order)
            .map(child => (
              <TreeItem key={child.id} node={child} onTopicClick={onTopicClick} />
            ))}
        </div>
      )}
    </div>
  );
}

export function TopicTree({ nodes, onTopicClick }: TopicTreeProps) {
  const sortedNodes = [...nodes].sort((a, b) => a.display_order - b.display_order);

  if (sortedNodes.length === 0) {
    return (
      <div className="text-center py-12 text-white/30 font-marathi text-sm">
        अभ्यासक्रम अद्याप जोडलेला नाही
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {sortedNodes.map(node => (
        <TreeItem key={node.id} node={node} onTopicClick={onTopicClick} />
      ))}
    </div>
  );
}
