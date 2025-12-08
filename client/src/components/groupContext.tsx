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
    const [activeGroup, setActiveGroup] = useState<Group | null>(() => {
        // Initialize from localStorage on mount
        try {
            const stored = localStorage.getItem('activeGroup');
            return stored ? JSON.parse(stored) : null;
        } catch (err) {
            console.error('Error loading active group from localStorage:', err);
            return null;
        }
    });

    const setActiveGroupWithPersistence = (group: Group | null) => {
        setActiveGroup(group);
        // Persist to localStorage
        try {
            if (group) {
                localStorage.setItem('activeGroup', JSON.stringify(group));
            } else {
                localStorage.removeItem('activeGroup');
            }
        } catch (err) {
            console.error('Error saving active group to localStorage:', err);
        }
    };

    return (
        <GroupContext.Provider value={{ activeGroup, setActiveGroup: setActiveGroupWithPersistence }}>
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