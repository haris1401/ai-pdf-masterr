const { createApp, ref, onMounted } = Vue;

createApp({
    setup() {
        const agents = ref([]);
        const tasks = ref([]);
        const metrics = ref([]);
        const loading = ref(false);

        const fetchAgents = async () => {
            try {
                const response = await axios.get('/agents');
                agents.value = response.data;
            } catch (error) {
                console.error("Error fetching agents:", error);
            }
        };

        const fetchTasks = async () => {
            try {
                const response = await axios.get('/tasks');
                tasks.value = response.data;
            } catch (error) {
                console.error("Error fetching tasks:", error);
            }
        };

        const fetchMetrics = async () => {
            try {
                const response = await axios.get('/metrics');
                metrics.value = response.data;
            } catch (error) {
                console.error("Error fetching metrics:", error);
            }
        };

        const refreshData = async () => {
            loading.value = true;
            await Promise.all([fetchAgents(), fetchTasks(), fetchMetrics()]);
            loading.value = false;
        };

        const assignTask = async (agentType) => {
            let description = "";
            const random = Math.random();
            
            if (agentType === 'sales') {
                if (random < 0.25) description = "Reach out to lead: John Doe (john@example.com)";
                else if (random < 0.5) description = "Answer pricing query for Enterprise plan";
                else if (random < 0.75) description = "Answer product query about AI features";
                else description = "Customer wants to purchase. Schedule appointment.";
            } else if (agentType === 'support') {
                if (random < 0.33) description = "Answer product query: How to reset password?";
                else if (random < 0.66) description = "Fetch ticket update for #404";
                else description = "Issue unresolved. Create ticket for login error.";
            } else if (agentType === 'operations') {
                if (random < 0.33) description = "Monitor SLA status";
                else if (random < 0.66) description = "Report system errors";
                else description = "Manage background tasks and resources";
            }

            try {
                await axios.post('/tasks', {
                    description: description,
                    agent_type: agentType
                });
                // Refresh data immediately to show pending task
                refreshData();
            } catch (error) {
                alert("Failed to assign task: " + error.response.data.detail);
            }
        };

        const getAgentName = (agentId) => {
            const agent = agents.value.find(a => a.id === agentId);
            return agent ? agent.name : 'Unknown Agent';
        };

        const getStatusColor = (status) => {
            switch(status) {
                case 'completed': return 'text-green-500 font-bold';
                case 'failed': return 'text-red-500 font-bold';
                case 'pending': return 'text-yellow-500 font-bold';
                default: return 'text-gray-500';
            }
        };
        
        const formatDate = (dateString) => {
            if (!dateString) return 'Never';
            return new Date(dateString).toLocaleTimeString();
        };

        onMounted(() => {
            refreshData();
            // Auto-refresh every 3 seconds
            setInterval(refreshData, 3000);
        });

        return {
            agents,
            tasks,
            metrics,
            loading,
            refreshData,
            assignTask,
            getAgentName,
            getStatusColor,
            formatDate
        };
    }
}).mount('#app');
