import React, { createContext, useContext, useState } from 'react';

interface Group {
    ID: number;
    name: string;
    description: string;
}

interface GroupContextType {
    activeGroup: Group | null;
    setActiveGroup: (group: Group | null) => void;
}

const GroupContext = createContext<GroupContextType | undefined>(undefined);

export function GroupProvider({ children }: { children: React.ReactNode }) {
    const [activeGroup, setActiveGroup] = useState<Group | null>(null);

    return (
        <GroupContext.Provider value={{ activeGroup, setActiveGroup }}>
            {children}
        </GroupContext.Provider>
    );
}

export function useGroup() {
    const context = useContext(GroupContext);
    if (context === undefined) {
        throw new Error('useGroup must be used within a GroupProvider');
    }
    return context;
}