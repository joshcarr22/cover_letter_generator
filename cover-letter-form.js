// Cover Letter Generator Form Handler
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('cover-letter-form');
    const resultDiv = document.getElementById('result');
    
    // Replace with your actual API URL
    const API_BASE_URL = 'https://cover-letter-generator-2.onrender.com';  // Update this to your Render URL
    // For local testing: const API_BASE_URL = 'http://localhost:5000';
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Show loading state
        resultDiv.innerHTML = '<div style="color: blue;">🔄 Processing your request...</div>';
        
        // Get form data
        const formData = new FormData(form);
        
        try {
            // Send request to Flask API
            const response = await fetch(`${API_BASE_URL}/process-cover-letter`, {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Success - display the generated cover letter
                resultDiv.innerHTML = `
                    <div style="color: green; margin-bottom: 20px;">
                        ✅ <strong>Cover Letter Generated Successfully!</strong>
                    </div>
                    
                    <div style="border: 1px solid #ddd; padding: 15px; background-color: #f9f9f9; margin-bottom: 20px;">
                        <h3>Job Details Extracted:</h3>
                        <p><strong>Title:</strong> ${result.job_data.job_title || 'Not specified'}</p>
                        <p><strong>Company:</strong> ${result.job_data.company_name || 'Not specified'}</p>
                        <p><strong>Skills Required:</strong> ${Array.isArray(result.job_data.skills) ? result.job_data.skills.join(', ') : 'Not specified'}</p>
                    </div>
                    
                    <div style="border: 1px solid #ddd; padding: 15px; background-color: #f0f8ff;">
                        <h3>Your Personalized Cover Letter:</h3>
                        <div style="white-space: pre-wrap; font-family: 'Times New Roman', serif; line-height: 1.6;">
                            ${result.cover_letter}
                        </div>
                    </div>
                    
                    <div style="margin-top: 15px;">
                        <button onclick="copyToClipboard()" style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; cursor: pointer;">
                            📋 Copy Cover Letter
                        </button>
                        <button onclick="downloadAsText()" style="background-color: #008CBA; color: white; padding: 10px 20px; border: none; cursor: pointer; margin-left: 10px;">
                            💾 Download as TXT
                        </button>
                    </div>
                `;
                
                // Store the cover letter for copy/download functions
                window.generatedCoverLetter = result.cover_letter;
                
            } else {
                // Error from API
                resultDiv.innerHTML = `
                    <div style="color: red;">
                        ❌ <strong>Error:</strong> ${result.error}
                    </div>
                `;
            }
            
        } catch (error) {
            // Network or other errors
            console.error('Error:', error);
            resultDiv.innerHTML = `
                <div style="color: red;">
                    ❌ <strong>Network Error:</strong> Unable to connect to the server. 
                    Please check your internet connection and try again.
                </div>
            `;
        }
    });
});

// Helper function to copy cover letter to clipboard
function copyToClipboard() {
    if (window.generatedCoverLetter) {
        navigator.clipboard.writeText(window.generatedCoverLetter).then(function() {
            alert('Cover letter copied to clipboard!');
        }).catch(function(err) {
            console.error('Could not copy text: ', err);
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = window.generatedCoverLetter;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            alert('Cover letter copied to clipboard!');
        });
    }
}

// Helper function to download cover letter as text file
function downloadAsText() {
    if (window.generatedCoverLetter) {
        const blob = new Blob([window.generatedCoverLetter], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `cover_letter_${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }
} 