import React from 'react';

const containerStyle = {
  fontFamily: 'Arial, sans-serif',
  margin: '20px',
  padding: '20px',
  lineHeight: '1.6',
  color: '#333',
};

const headerStyle = {
  padding: '5px 0px',
  borderRadius: '5px',
  marginBottom: '20px',
};

const sectionStyle = {
  marginBottom: '20px',
};

const codeStyle = {
  backgroundColor: '#e8e8e8',
  padding: '5px 10px',
  borderRadius: '3px',
  fontFamily: 'monospace',
};

const BetBotRequestFormats = () => {
  return (
    <div style={containerStyle}>
      <h1 style={headerStyle}>BetBotX Twitter (X) Request Formatting Explained</h1>

      <section style={sectionStyle}>
        <h2>Market Creation Template</h2>
        <p>
          The basic structure for create market requests to <code style={codeStyle}>@betbotx</code> is as follows:
        </p>
        <p style={codeStyle}>
          @betbotx create &lt;type&gt; &lt;sport&gt; &lt;identifier&gt; &lt;condition&gt; &lt;time UTC&gt;
        </p>
        <p>
          Each placeholder represents:
        </p>
        <ul>
          <li><strong>&lt;type&gt;</strong>: The bet type (e.g., <code>sport</code>, <code>crypto</code>. Coming soon <code>politics</code>, <code>weather</code>, <code>stocks</code>, and many more.</li>
          <li><strong>&lt;sport&gt;</strong>: For sports bets, this is the sport type. Supported sports include NBA, MLS, MLB, EFL Cup, and EPL. Crypto is explained below.</li>
          <li><strong>&lt;identifier&gt;</strong>: The team name or asset identifier.</li>
          <li><strong>&lt;condition&gt;</strong>: The condition for the bet (for example, a win or a greater than / less than symbol followed by a value to indicate a score spread).</li>
          <li><strong>&lt;time UTC&gt;</strong>: The time of the event in UTC (format: YYYY-MM-DD HH:MM:SS).</li>
        </ul>
      </section>

      <section style={sectionStyle}>
        <p>
          <strong>1. Standard Sport Market Creation:</strong>
        </p>
        <p style={codeStyle}>
          @betbotx create sport NBA New York Knics win 2025-03-01 12:00:00
        </p>
        <ul>
          <li><strong>create:</strong> Action to create a bet.</li>
          <li><strong>sport:</strong> Indicates that this is a sports bet.</li>
          <li><strong>NBA:</strong> The league (supported sports include NBA, MLS, MLB, EFL Cup, EPL).</li>
          <li><strong>New York Knics:</strong> The team name (note: adjust spelling as needed).</li>
          <li><strong>win:</strong> The condition, indicating that the bet is on the team to win.</li>
          <li><strong>2024-03-01 12:00:00:</strong> The event time in UTC.</li>
        </ul>

        <p>
          <strong>2. Sport Market with a Numerical Condition:</strong>
        </p>
        <p style={codeStyle}>
          @betbotx create sport NBA New York Knics {'>'} 10 2025-03-01 12:00:00
        </p>
        <ul>
          <li><strong>&gt; 10:</strong> Specifies a condition where the outcome should exceed 10 (e.g., points scored). Here the bet is that the Knicks will win by more than 10 points.</li>
        </ul>

        <p>
          <strong>3. Cryptocurrency Market Creation:</strong>
        </p>
        <p style={codeStyle}>
          @betbotx create crypto ethereum {'>'} 2600 2025-03-05 12:00:00
        </p>
        <ul>
          <li><strong>&gt; 2600:</strong> Indicates whether the price of ethereum will be above 2600 by March 5th 12pm UTC.</li>
        </ul>

        <h2>Bet Placement Template</h2>


        <p>
          The basic structure for placing bet requests to <code style={codeStyle}>@betbotx</code> is as follows:
        </p>
        <p style={codeStyle}>
          @betbotx bet &lt;market name&gt; &lt;amount&gt; &lt;outcome&gt;
        </p>
        <p>
          Each placeholder represents:
        </p>
        <ul>
          <li><strong>&lt;market name&gt;</strong>: This is the direct market name from the create market request.</li>
          <li><strong>&lt;amount&gt;</strong>: Amount of NEAR tokens to bet.</li>
          <li><strong>&lt;outcome&gt;</strong>: Bet prediction - either <code>yes</code> or <code>no</code></li>
        </ul>

        <p>
          <strong>1. Betting Example:</strong>
        </p>
        <p style={codeStyle}>
          @betbotx bet sport MLS LA Galaxy {'>'} 1 1.4 yes
        </p>
        <ul>
          <li><strong>bet:</strong> Action to place a bet.</li>
          <li><strong>MLS LA Galaxy {'>'} 1:</strong> Full market name.</li>
          <li><strong>1.4:</strong> NEAR tokens placed on bet.</li>
          <li><strong>yes:</strong> Betting on an outcome of yes.</li>
        </ul>
      </section>

      <section style={sectionStyle}>
        <h2>Other Commands</h2>
        <p>
          The bot supports additional commands:
        </p>
        <ul>
          <li style={codeStyle}>
            @betbotx markets
          </li>
          <li>
            <strong>markets:</strong> Returns a list of all currently active betting markets.
          </li>
          <li style={codeStyle}>
            @betbotx bets &lt;address&gt;
          </li>
          <li>
            <strong>bets:</strong> Retrieves all bets associated with the provided address.
          </li>
          <li style={codeStyle}>
            @betbotx market sport NBA New York Knics win
          </li>
          <li>
            <strong>market:</strong> Retrieves detailed market information for a specific market by the name: <code>sport NBA New York Knics win</code>.
          </li>
        </ul>
      </section>

      <section style={sectionStyle}>
        <h2>Example Requests for Crypto</h2>
        <p>
          For crypto bets, the template remains largely the same. Here’s an example:
        </p>
        <p style={codeStyle}>
          @betbotx create crypto bitcoin {'>'} 50000 2024-04-15 15:30:00
        </p>
        <ul>
          <li><strong>crypto:</strong> Indicates that this is a cryptocurrency bet.</li>
          <li><strong>BTC Bitcoin:</strong> The crypto asset (you can use symbols or full names).</li>
          <li><strong>&gt; 50000:</strong> The condition (e.g., price should be greater than 50000).</li>
          <li><strong>2024-04-15 15:30:00:</strong> The target time in UTC.</li>
        </ul>
        <p>
          Using CoinGecko API for price data, the bot will resolve the bet based on the price at the specified time. Visit the following list to ensure that the asset is supported and make sure to use the API id value for bet creation: https://docs.google.com/spreadsheets/d/1wTTuxXt8n9q7C4NDXqQpI3wpKu1_5bGVmP9Xz0XGSyU/edit?gid=0#gid=0.
        </p>
      </section>

      <section style={sectionStyle}>
        <h2>Supported Sports</h2>
        <p>
          For sports bets, the following leagues are supported:
        </p>
        <ul>
          <li>NBA</li>
          <li>MLS</li>
          <li>MLB</li>
          <li>EFL Cup</li>
          <li>EPL</li>
        </ul>
      </section>

      <footer style={{ marginTop: '40px', fontSize: '0.9em', color: '#777' }}>
        <p>Created by the BetBotX team. For more details, refer to the bot documentation.</p>
      </footer>
    </div>
  );
};

export default BetBotRequestFormats;
