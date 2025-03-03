import React from "react";
import ReactDOM from "react-dom";
import "./index.css";
import App from "./App";
import Explainer from "./explainer";
import { setupWalletSelector } from "@near-wallet-selector/core";
import { setupHereWallet } from "@near-wallet-selector/here-wallet";
import { setupMyNearWallet } from "@near-wallet-selector/my-near-wallet";
import { setupNearWallet } from "@near-wallet-selector/near-wallet";
import { setupNeth } from "@near-wallet-selector/neth";
import { setupNightly } from "@near-wallet-selector/nightly";
import { setupSender } from "@near-wallet-selector/sender";
import { WalletSelector } from "@near-wallet-selector/core";

async function init() {
  return setupWalletSelector({
    network: "testnet",
    modules: [
      setupNearWallet(),
      setupMyNearWallet(),
      setupSender(),
      setupHereWallet(),
      setupNightly(),
      setupNeth(),
    ]
  });
}

const initializeNear = async () => {
  try {
    const selector = await init();
    const state = selector.store.getState();
    const currentUser = state.accounts.length > 0 ? state.accounts[0].accountId : undefined;

    renderApp(selector, currentUser);
  } catch (error) {
    console.error('Error initializing NEAR:', error);
  }
};

initializeNear();

const renderApp = (selector: WalletSelector, currentUser?: string) => {
  ReactDOM.render(
    <React.StrictMode>
      <App selector={selector} currentUser={currentUser} />
      <Explainer />
    </React.StrictMode>,
    document.getElementById("root")
  );
};