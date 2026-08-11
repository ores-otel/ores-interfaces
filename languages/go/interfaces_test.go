package oresinterfaces
import "testing"
func TestBiometricProofRejectsRawMaterial(t *testing.T) {
    if !(PlatformBiometricProof{VerifiedByPlatformAuthenticator:true, UserVerification:"required"}).Safe() { t.Fatal("safe platform proof rejected") }
    if (PlatformBiometricProof{VerifiedByPlatformAuthenticator:true, UserVerification:"required", RawBiometricMaterialPresent:true}).Safe() { t.Fatal("raw material accepted") }
}
func TestGlobalRevocationRequiresPhishingResistantAAL2WebAuthn(t *testing.T) {
    stepUp := RevocationStepUp{Assurance:Aal2, AuthMethods:[]AuthMethod{AuthMethodWebAuthn}, PhishingResistant:true}
    if !stepUp.Sufficient() { t.Fatal("valid revocation step-up rejected") }
    stepUp.Assurance = Aal1
    if stepUp.Sufficient() { t.Fatal("AAL1 revocation step-up accepted") }
}
func TestPartialRevocationIsTerminal(t *testing.T) {
    if !RevocationPartial.Terminal() || RevocationRunning.Terminal() { t.Fatal("revocation terminal-state drift") }
    if RevocationInteractiveSessions != "interactive_sessions" { t.Fatal("revocation scope drift") }
}
