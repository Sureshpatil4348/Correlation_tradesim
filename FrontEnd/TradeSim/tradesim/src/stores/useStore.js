// /stores/useStore.js
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

const useStore = create(
    persist(
        (set) => ({
            isLoggedIn: false,  // To track if the user is logged in
            accountInfo: null,  // To store the account information
            isLoading: false,
            startActiveStrategy: false,
            setStartActiveStrategy: (startActiveStrategy) => set({ startActiveStrategy }),
            setIsLoading: (isLoading) => set({ isLoading }),
            setIsLoggedIn: (isLoggedIn) => set({ isLoggedIn }),
            setAccountInfo: (accountInfo) => set({ accountInfo }),
            strategies: [],
            setStrategies: (strategies) => set({ strategies }),
            strategyToBackTest: null,
            setStrategyToBackTest: (strategyToBackTest) => set({ strategyToBackTest }),
            // Action to login and set account info
            login: (accountInfo) => set({ isLoggedIn: true, accountInfo }),

            // Action to logout and reset the account info
            logout: () => set({ isLoggedIn: false, accountInfo: null }),

            selectedPage: 'Dashboard',
            setSelectedPage: (page) => set({ selectedPage: page }),
        }), {
        name: 'trade-sim-store',
        storage: createJSONStorage(() => localStorage),
    })
);

export default useStore;
